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
        motion = f"{int(self.motion):02x}0000"

        return header + combo + endtime + splits_pt1 + name + country + motion + splits_pt2 + ".dat"

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

        size = int.to_bytes(len(self.data) + 0x48, 4, "big")
        crc = crc32(self.data).to_bytes(4, "big")

        return b'CTG0' + ver + size + (b'\0' * 0x2C) + crc + (b'\0' * 0x0C)

    def __init__(self, data: bytes, motion=False, lang: str = "en"):
        # Ghost data in Mario Kart 8 for the most part is formatted as Big-Endian
        # The embedded Mii data seems to be formatted as Little-Endian, however
        if data[0x0:0x4].decode('utf8') == "CTG0":
            self.data = data[0x48:]
            self.header = data[:0x48]
        else:
            self.data = data
            self.header = self.generate_header()

        if self.data[0x0:0x6] != b'\x00\x00\x04\x00\x03\xa0':
            raise InvalidGhostFormat(
                "Ghost not in the proper format: likely not a Mario Kart 8 ghost"
            )

        self.motion = motion  # Still being investigated if this exists internally
        version = self.data[0x06:0x08]
        self.version = self._versions.get(version, "???")

        # Timestamp
        self.year = int.from_bytes(self.data[0x0E:0x10], "big")
        self.month = self.data[0x13]
        self.day = self.data[0x17]
        self.weekday = common.Weekdays(self.data[0x1B])
        self.hour = self.data[0x1F]
        self.min = self.data[0x23]
        self.sec = self.data[0x27]

        # Combo Info
        self.character = common.Characters(self.data[0x3B])
        self.variant = self.data[0x3C]
        self.mii_weight = self.data[0x3D]
        self.vehicle_body = common.MK8VehicleBodies(self.data[0x2F])
        self.tire = common.Tires(self.data[0x33])
        self.glider = common.Gliders(self.data[0x37])

        # Race Settings
        self.track = common.MK8Tracks(self.data[0x17F])
        self.online = bool(self.data[0x183])
        self.gamemode = self.data[0x187]
        self.num_racers = self.data[0x18B]

        cc_id = self.data[0x193]
        if cc_id < len(self._engine_classes):
            self.engine_class = self._engine_classes[cc_id]
        else:
            self.engine_class = "???"

        self.mirror = bool(self.data[0x194])
        self.team = self.data[0x195]

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

        # Total Time and Splits
        self.total_time = MK8TimeTuple(
            self.data[0x36D], self.data[0x36E], int.from_bytes(self.data[0x370:0x372], "big")
        )

        lap_offsets = [0x331, 0x33D, 0x349, 0x355, 0x361, 0x385, 0x391]
        if self.track != common.MK8Tracks.GCN_BABY_PARK:
            lap_offsets = lap_offsets[:3]

        self.lap_times = [MK8TimeTuple(self.data[x], self.data[x + 1], int.from_bytes(self.data[x + 3:x + 5], "big"))
                          for x in lap_offsets]

    def __str__(self):
        return (
            f"Track: {self.track.fullname}\n"
            f"Engine Class: {self.engine_class}\n"
            f"Version: {self.version}\n\n"
            f"Total Time: {self.total_time}\n"
            f"Lap Times: {' | '.join(str(time) for time in self.lap_times)}\n"
            f"Motion Controls: {self.motion}\n"
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
