from binascii import crc32
from typing import Literal
from uuid import UUID

from mk8boards import common
from mk8boards.miis import MiiDataSwitch
from mk8boards.common import InvalidGhostFormat, MK8TimeTuple


class MK8DXPlayerInfo:
    def __init__(self, common_data: bytes, lang: str = 'en'):
        self.mii = MiiDataSwitch.parse(common_data[0x14:0x6C])
        self.country_id = common_data[0x70:0x72].decode()[::-1]
        self.profile_id = UUID(bytes_le=common_data[0xC0:0xD0])

    def __str__(self):
        return ''.join(f"{k}: {v}\n" for k, v in self.__dict__.items())


class MK8DXGhostInfo:
    _engine_classes = ("50cc", "100cc", "150cc", "200cc")

    def generate_filename(self, prefix: Literal['sg', 'fg', 'dg'] = 'sg',
                          staff_ghost: bool = False, slot: int = 0) -> str:
        # Refer to the following link for the full breakdown of the filename structures:
        # https://github.com/Dinostraw/MK8Leaderboards/wiki/Ghost-Data-(Deluxe)#filename-formats
        if prefix not in ('sg', 'fg', 'dg'):
            raise ValueError("Prefix must either be 'sg', 'fg', or 'dg'")

        # Ghosts created in-game have very short filenames
        if not staff_ghost:
            if prefix == 'dg':
                order = slot  # Can be anything from 0 to 31 inclusive
            elif self.track <= common.MK8Tracks.BIG_BLUE:
                order = self.track - 0x10
            else:
                order = self.track - 0x1B
            return f"{prefix}{order:02d}.dat"

        # Staff ghosts have a much more complicated filename format
        # For the 48 base-game tracks (Big Blue has the highest ID of these)
        if self.track <= common.MK8Tracks.BIG_BLUE:
            header = f"{prefix}{self.track-0x10:02x}{self.track:02x}"
        # For the DLC tracks
        else:
            header = f"{prefix}{self.track-0x1B:02x}{self.track:02x}"

        character = f"{self.character:02x}{self.variant:02x}{self.mii_weight:02x}"
        combo = f"{character}{self.vehicle_body:02x}{self.tire:02x}{self.glider:02x}"

        endtime = f'{self.total_time.mins:01x}{self.total_time.secs:02x}{self.total_time.msecs:03x}'

        if self.track == common.MK8Tracks.GCN_BABY_PARK:
            splits = ''.join([f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times])
        else:
            filler = "000000" * 4  # Four filler splits, each represents a time of 0:00.000
            splits = (''.join(f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times[:3])
                      + filler)  # Since most tracks have just 3 laps, append filler

        pnb = self.player_name_bytes
        # Convert each UTF-16 character's byte order from little-endian to big-endian and join them
        name = ''.join(f"{pnb[x+1]:02x}{pnb[x]:02x}" for x in range(0, len(pnb), 2))
        country = ''.join(f'{ord(x):02x}' for x in self.country_id)
        motion = f'{self.motion:02x}'

        return header + combo + endtime + splits + name + country + motion + '0000.dat'

    def generate_header(self) -> bytes:
        ver = b'\x00\x00\x00\x00'
        size = int.to_bytes(len(self.data) + 0x48, 4, 'little')
        crc = crc32(self.data).to_bytes(4, 'little')

        return b'0GTC' + ver + size + (b'\0' * 0x2C) + crc + (b'\0' * 0x0C)

    def __init__(self, data: bytes, lang: str = "en"):
        # Ghost data in Mario Kart 8 Deluxe follows a Little-Endian format
        if data[0x0:0x4] == b'0GTC':
            self.data = data[0x48:]
            self.header = data[:0x48]
        else:
            self.data = data
            self.header = self.generate_header()

        if self.data[0x0:0x8] != b'\x00\x0C\x00\x00\x00\x00\x20\x00':
            raise InvalidGhostFormat(
                "Ghost not in the proper format: likely not a Mario Kart 8 Deluxe ghost"
            )

        # Timestamp
        self.year = int.from_bytes(self.data[0x0C:0x10], 'little')
        self.month = int.from_bytes(self.data[0x10:0x14], 'little')
        self.day = int.from_bytes(self.data[0x14:0x18], 'little')
        self.weekday = common.Weekdays(int.from_bytes(self.data[0x18:0x1C], 'little'))
        self.hour = int.from_bytes(self.data[0x1C:0x20], 'little')
        self.min = int.from_bytes(self.data[0x20:0x24], 'little')
        self.sec = int.from_bytes(self.data[0x24:0x28], 'little')

        # Race Settings
        # Technically signed, but treating as unsigned to simplify processing
        cc_id = int.from_bytes(self.data[0x3C:0x40], 'little')
        if cc_id < len(self._engine_classes):
            self.engine_class = self._engine_classes[cc_id]
        else:
            self.engine_class = "???"

        # Combo Info
        self.character = common.Characters(int.from_bytes(self.data[0x68:0x6C], 'little', signed=True))
        self.variant = self.data[0x6C]
        self.mii_weight = self.data[0x6D]
        self.vehicle_body = common.MK8DXVehicleBodies(int.from_bytes(
            self.data[0x5C:0x60], 'little', signed=True
        ))
        self.tire = common.Tires(int.from_bytes(self.data[0x60:0x64], 'little', signed=True))
        self.glider = common.Gliders(int.from_bytes(self.data[0x64:0x68], 'little', signed=True))

        # Basic Info
        track = int.from_bytes(self.data[0x1CC:0x1D0], 'little', signed=True)
        if track <= common.MK8Tracks.BIG_BLUE:
            self.track = common.MK8Tracks(track)
        else:
            self.track = common.BoosterTracks(track)

        # Mii data
        self.mii = MiiDataSwitch.parse(self.data[0x244:0x29C])

        # Country Info
        self.country_id = self.data[0x2A0:0x2A2].decode()[-1::-1]

        # Player Name
        self.player_name_bytes = self.data[0x300:0x314]
        # Strip everything after the null character if one occurs
        self.player_name = self.player_name_bytes.decode("utf-16-le").split("\0", 1)[0]

        # Total Time and Splits
        self.total_time = MK8TimeTuple(
            self.data[0x384], self.data[0x385], int.from_bytes(self.data[0x386:0x388], 'little')
        )

        lap_offsets = [0x334, 0x33C, 0x344, 0x34C, 0x354, 0x35C, 0x364]
        if self.track != common.MK8Tracks.GCN_BABY_PARK:
            lap_offsets = lap_offsets[:3]

        self.lap_times = [MK8TimeTuple(self.data[x], self.data[x+1], int.from_bytes(self.data[x+2:x+4], 'little'))
                          for x in lap_offsets]

        # Various Race Flags
        self.motion = (self.data[0x389] >> 1) & 0b00000011

        # Filename and File Version
        self.filename_version = self.data[0x390]
        self.file_version = self.data[0x391]

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
            f"Total Time: {self.total_time}\n"
            f"Lap Times: {' | '.join(str(time) for time in self.lap_times)}\n"
            f"Motion Controls: {motion_kind}\n"
            f"\n"
            f"Name: {self.player_name}\n"
            f"Country: {self.country_id}\n"
            f"Timestamp: {str(self.weekday.name).title()}, "
            f"{self.year}-{self.month:02d}-{self.day:02d}, "
            f"{self.hour:02d}:{self.min:02d}:{self.sec:02d} LT\n"
            f"\n"
            f"Character: {str(self.character.name).replace('_', ' ').title()}\n"
            f"Variant: {self.variant}\n"
            f"Mii Weight Class: {self.mii_weight}\n"
            f"Combo: {str(self.vehicle_body.name).replace('_', ' ').title()}, "
            f"{str(self.tire.name).replace('_', ' ').title()}, "
            f"{str(self.glider.name).replace('_', ' ').title()}"
        )
