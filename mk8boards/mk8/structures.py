import calendar
from binascii import crc32
from typing import Literal
from uuid import UUID

from mk8boards import common
from mk8boards.common import InvalidGhostFormat, MK8TimeTuple
from mk8boards.miis import MiiDataWiiU
from mk8boards.mk8.countries import CountryMap


class MK8PlayerInfo:
    def __init__(self, common_data: bytes, lang: str = "en"):
        # User Mii Info
        self.mii = MiiDataWiiU.parse(common_data[0x14:0x74])

        # Location: Country Info
        self.country_id = common_data[0x74]
        country_data = CountryMap.get_country(self.country_id)
        self.country_code = country_data.alpha3
        self.country = country_data.names[lang]

        # Location: Region Info
        self.subregion_id = common_data[0x75]
        subregion_data = CountryMap.get_subregion(self.country_id, self.subregion_id)
        self.subregion = subregion_data.names[lang]

        self.profile_id = UUID(bytes=common_data[0xC4:0xD4])

    def __str__(self):
        return ''.join(f"{k}: {v}\n" for k, v in self.__dict__.items())


class MK8GhostInfo:
    _engine_classes = ("50cc", "100cc", "150cc", "200cc")
    _versions = {b'\x00\x00': "1.0", b'\x00\x01': "2.0", b'\x00\x02': "3.0", b'\x08\x00': "4.0 / 4.1 / 4.2"}

    def generate_filename(self, prefix: Literal['dg', 'gs', 'sg'] = 'dg', slot: int = 0) -> str:
        # Based on the information gathered in this forum post:
        # https://gbatemp.net/threads/post-your-wiiu-cheat-codes-here.395443/post-8640417

        # Refer to the following link for the full breakdown of the filename structure:
        # https://github.com/Dinostraw/MK8Leaderboards/wiki/Ghost-Data-(Wii-U)#filename-format
        if prefix not in ('dg', 'gs', 'sg'):
            raise ValueError("Prefix must either be 'dg', 'gs', or 'sg'")

        if prefix == 'dg':
            # The 00 can be anything from 00 to 0f inclusive
            header = f"{prefix}{slot:02x}{self.track:02x}"
        else:
            header = f"{prefix}{self.track-0x10:02x}{self.track:02x}"

        character = f"{self.character:02x}{self.variant:02x}{self.mii_weight:02x}"
        combo = f"{character}{self.vehicle_body:02x}{self.tire:02x}{self.glider:02x}"

        endtime = f'{self.total_time.mins:01x}{self.total_time.secs:02x}{self.total_time.msecs:03x}'

        if self.track == common.MK8Tracks.GCN_BABY_PARK:
            splits_pt1 = ''.join([f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times[:5]])
            splits_pt2 = ''.join([f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times[5:]])
        else:
            splits_pt2 = "93b3e7" * 2  # Two filler splits, each represents a time of 9:59.999
            splits_pt1 = (''.join(f"{t.mins:01x}{t.secs:02x}{t.msecs:03x}" for t in self.lap_times[:3])
                          + splits_pt2)  # Since most tracks have just 3 laps, append filler

        name = ''.join(f"{b:02x}" for b in self.player_name_bytes)
        country = f"{self.country_id:02x}"
        motion = f'{self.motion:02x}'

        if self.filename_version < 0x0A:
            # 0-9
            filename_ver = f'{chr(0x30 + self.filename_version)}000'
        elif self.filename_version < 0x23:
            # a-y
            filename_ver = f'{chr(0x57 + self.filename_version)}000'
        else:
            filename_ver = 'z000'

        return header + combo + endtime + splits_pt1 + name + country + motion + filename_ver + splits_pt2 + '.dat'

    def generate_header(self, version: str = '4.2') -> bytes:
        if version == '4.2' or version == '4.1':
            ver = b'\x04\x01\x00\x04'
        elif version == '4.0':
            ver = b'\x04\x00\x00\x03'
        elif version == '3.0':
            ver = b'\x03\x00\x00\x02'
        elif version == '2.0':
            ver = b'\x02\x00\x00\x01'
        else:
            ver = b'\x00\x10\x00\x10'

        size = int.to_bytes(len(self.data) + 0x48, 4, 'big')
        crc = crc32(self.data).to_bytes(4, 'big')

        return b'CTG0' + ver + size + (b'\0' * 0x2C) + crc + (b'\0' * 0x0C)

    def __init__(self, data: bytes, lang: str = "en"):
        # Ghost data in Mario Kart 8 for the most part is formatted as Big-Endian
        # The embedded Mii data seems to be formatted as Little-Endian, however
        if data[0x0:0x4] == b'CTG0':
            self.data = data[0x48:]
            self.header = data[:0x48]
        else:
            self.data = data
            self.header = self.generate_header()

        if self.data[0x0:0x6] != b'\x00\x00\x04\x00\x03\xa0':
            raise InvalidGhostFormat(
                "Ghost not in the proper format: likely not a Mario Kart 8 ghost"
            )

        version = self.data[0x06:0x08]
        self.version = self._versions.get(version, "???")

        # Timestamp
        self.year = int.from_bytes(self.data[0x0C:0x10], 'big')
        self.month = int.from_bytes(self.data[0x10:0x14], 'big')
        self.day = int.from_bytes(self.data[0x14:0x18], 'big')
        self.weekday = common.Weekdays(int.from_bytes(self.data[0x18:0x1C], 'big'))
        self.hour = int.from_bytes(self.data[0x1C:0x20], 'big')
        self.min = int.from_bytes(self.data[0x20:0x24], 'big')
        self.sec = int.from_bytes(self.data[0x24:0x28], 'big')

        # Combo Info
        self.character = common.Characters(int.from_bytes(self.data[0x38:0x3C], 'big', signed=True))
        self.variant = self.data[0x3C]
        self.mii_weight = self.data[0x3D]
        self.vehicle_body = common.MK8VehicleBodies(int.from_bytes(self.data[0x2C:0x30], 'big', signed=True))
        self.tire = common.Tires(int.from_bytes(self.data[0x30:0x34], 'big', signed=True))
        self.glider = common.Gliders(int.from_bytes(self.data[0x34:0x38], 'big', signed=True))

        # Race Settings
        self.track = common.MK8Tracks(int.from_bytes(self.data[0x17C:0x180], 'big', signed=True))
        self.online = bool(int.from_bytes(self.data[0x180:0x184], 'big', signed=True))
        self.gamemode = int.from_bytes(self.data[0x184:0x188], 'big', signed=True)

        # Technically signed, but treating as unsigned to simplify processing
        cc_id = int.from_bytes(self.data[0x190:0x194], 'big')
        if cc_id < len(self._engine_classes):
            self.engine_class = self._engine_classes[cc_id]
        else:
            self.engine_class = "???"

        self.mirror = bool(self.data[0x194])
        self.teams = bool(self.data[0x195])
        self.num_racers = int.from_bytes(self.data[0x1A8:0x1AC], 'big', signed=True)

        # Mii Data
        self.mii = MiiDataWiiU.parse(self.data[0x244:0x2A4])
        self.mii_crc16 = self.data[0x2A2:0x2A4]

        # Location: Country Info
        self.country_id = self.data[0x2A4]
        country_data = CountryMap.get_country(self.country_id)
        self.country_code = country_data.alpha3
        self.country = country_data.names[lang]

        # Location: Region Info
        self.subregion_id = self.data[0x2A5]
        subregion_data = CountryMap.get_subregion(self.country_id, self.subregion_id)
        self.subregion = subregion_data.names[lang]

        # Player Name
        self.player_name_bytes = self.data[0x304:0x318]
        # Force big endian; strip everything after the null character if one occurs
        self.player_name = self.player_name_bytes.decode("utf_16_be").split("\0", 1)[0]

        # Various Race Flags
        self.motion = (self.data[0x379] >> 5) & 0b00000011

        # Filename Version
        self.filename_version = self.data[0x380]

        # Total Time and Splits
        self.total_time = MK8TimeTuple(
            int.from_bytes(self.data[0x36C:0x36E], 'big'),
            self.data[0x36E],
            int.from_bytes(self.data[0x370:0x372], 'big')
        )

        lap_offsets = [0x330, 0x33C, 0x348, 0x354, 0x360, 0x384, 0x390]
        if self.track != common.MK8Tracks.GCN_BABY_PARK:
            lap_offsets = lap_offsets[:3]

        self.lap_times = [MK8TimeTuple(int.from_bytes(self.data[x:x + 2], 'big'),
                                       self.data[x + 2],
                                       int.from_bytes(self.data[x + 4:x + 6], 'big'))
                          for x in lap_offsets]

    def __str__(self):
        if self.motion == 0:
            motion_kind = 'False'
        elif self.motion == 1:
            motion_kind = 'True (Regular)'
        else:
            motion_kind = 'True (Gold)'

        return (
            f"Track: {self.track.fullname}\n"
            f"Engine Class: {self.engine_class}\n"
            f"Version: {self.version}\n\n"
            f"Total Time: {self.total_time}\n"
            f"Lap Times: {' | '.join(str(time) for time in self.lap_times)}\n"
            f"Motion Controls: {motion_kind}\n"
            f"\n"
            f"Name: {self.player_name}\n"
            f"Location: {self.subregion}, {self.country}\n"
            f"Timestamp: {str(self.weekday.name[:3]).title()}, "
            f"{self.day:02d} {calendar.month_abbr[self.month]} {self.year} "
            f"{self.hour:02d}:{self.min:02d}:{self.sec:02d} LT\n"
            f"\n"
            f"Character: {str(self.character.name).replace('_', ' ').title()}\n"
            f"Variant: {self.variant}\n"
            f"Mii Weight Class: {self.mii_weight}\n"
            f"Combo: {str(self.vehicle_body.name).replace('_', ' ').title()}, "
            f"{str(self.tire.name).replace('_', ' ').title()}, "
            f"{str(self.glider.name).replace('_', ' ').title()}"
        )
