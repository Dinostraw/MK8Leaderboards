import re
from glob import glob
from typing import Literal, NamedTuple

from mk8boards import common
from mk8boards.miis import MiiDataSwitch, MiiDataWiiU
from mk8boards.mk8.countries import CountryMap


class InvalidGhostFormat(Exception):
    pass


class MK8TimeTuple(NamedTuple):
    mins: int
    secs: int
    msecs: int

    def __str__(self):
        return f"{self.mins}:{self.secs:02}.{self.msecs:03}"


class MK8PlayerInfo:
    def __init__(self, common_data: bytes, lang: str = "en"):
        # Location: Country Info
        self.country_id = common_data[0x74]
        country_data = CountryMap.get_country(self.country_id)
        self.country_code = country_data.alpha3
        self.country = country_data.names[lang]

        # Location: Region Info
        self.subregion_id = common_data[0x75]
        subregion_data = CountryMap.get_subregion(self.country_id, self.subregion_id)
        self.subregion = subregion_data.names[lang]

        # User Mii Info
        self.mii = MiiDataWiiU.parse(common_data[0x14:0x74])

    def __str__(self):
        return ''.join(f"{k}: {v}\n" for k, v in self.__dict__.items())


class MK8GhostInfo:
    def generate_filename(self, prefix: Literal['dg', 'gs', 'sg'] = 'dg') -> str:
        # Based on the information gathered in this forum post:
        # https://gbatemp.net/threads/post-your-wiiu-cheat-codes-here.395443/post-8640417

        # Refer to the following link for the full breakdown of the filename structure:
        # https://github.com/Dinostraw/MK8Leaderboards/wiki/Ghost-Data-(Wii-U)#filename-format
        if prefix not in ('dg', 'gs', 'sg'):
            raise ValueError("Prefix must either be 'dg', 'gs', or 'sg'")

        if prefix == 'dg':
            # The 00 can be anything from 00 to 0f inclusive
            header = f"{prefix}00{self.track.id_:02x}"
        else:
            header = f"{prefix}{self.track.id_-0x10:02x}{self.track.id_:02x}"

        character = f"{self.character.value:02x}{self.variant:02x}{self.mii_weight:02x}"
        combo = f"{character}{self.vehicle_body.value:02x}{self.tire.value:02x}{self.glider.value:02x}"

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

    def __init__(self, data: bytes, motion=False, lang: str = "en"):
        # Ghost data in Mario Kart 8 for the most part is formatted as Big-Endian
        # The embedded Mii data seems to be formatted as Little-Endian, however
        data = bytes(data)
        data = data[0x48:] if data[0x0:0x4].decode('utf8') == "CTG0" else data

        if data[0x0:0x6] != b'\x00\x00\x04\x00\x03\xa0':
            raise InvalidGhostFormat(
                "Ghost not in the proper format: likely not a Mario Kart 8 ghost"
            )

        # Basic Info
        self.track = common.MK8Tracks(data[0x17F])
        self.motion = motion  # Still being investigated if this exists internally
        self.player_name_bytes = data[0x304:0x318]
        # Force big endian; strip everything after the null character if one occurs
        self.player_name = self.player_name_bytes.decode("utf_16_be").split("\0", 1)[0]
        self.mii = MiiDataWiiU.parse(data[0x244:0x2A4])

        # Timestamp
        self.year = int.from_bytes(data[0x0E:0x10], "big")
        self.month = data[0x13]
        self.day = data[0x17]
        self.weekday = common.Weekdays(data[0x1B])
        self.hour = data[0x1F]
        self.min = data[0x23]
        self.sec = data[0x27]

        # Location: Country Info
        self.country_id = data[0x2A4]
        country_data = CountryMap.get_country(self.country_id)
        self.country_code = country_data.alpha3
        self.country = country_data.names[lang]

        # Location: Region Info
        self.subregion_id = data[0x2A5]
        subregion_data = CountryMap.get_subregion(self.country_id, self.subregion_id)
        self.subregion = subregion_data.names[lang]

        # Combo Info
        self.character = common.Characters(data[0x3B])
        self.variant = data[0x3C]
        self.mii_weight = data[0x3D]
        self.vehicle_body = common.MK8VehicleBodies(data[0x2F])
        self.tire = common.Tires(data[0x33])
        self.glider = common.Gliders(data[0x37])

        # Total Time and Splits
        self.total_time = MK8TimeTuple(data[0x36D], data[0x36E], int.from_bytes(data[0x370:0x372], "big"))

        lap_offsets = [0x331, 0x33D, 0x349, 0x355, 0x361, 0x385, 0x391]
        if self.track != common.MK8Tracks.GCN_BABY_PARK:
            lap_offsets = lap_offsets[:3]

        self.lap_times = [MK8TimeTuple(data[x], data[x+1], int.from_bytes(data[x+3:x+5], "big"))
                          for x in lap_offsets]

    def __str__(self):
        return (
            f"Track: {self.track.fullname}\n"
            f"Total Time: {self.total_time}\n"
            f"Lap times: {' | '.join(str(time) for time in self.lap_times)}\n"
            f"Motion Controls: {self.motion}\n"
            f"\n"
            f"Name: {self.player_name}\n"
            f"Location: {self.subregion}, {self.country}\n"
            f"Timestamp: {str(self.weekday.name).title()}, "
            f"{self.year}-{self.month:02d}-{self.day:02d}, "
            f"{self.hour:02d}:{self.min:02d}:{self.sec:02d}\n"
            f"\n"
            f"Character: {str(self.character.name).replace('_', ' ').title()}\n"
            f"Variant: {self.variant}\n"
            f"Mii Weight Class: {self.mii_weight}\n"
            f"Combo: {str(self.vehicle_body.name).replace('_', ' ').title()}, "
            f"{str(self.tire.name).replace('_', ' ').title()}, "
            f"{str(self.glider.name).replace('_', ' ').title()}"
        )


class MK8DXGhostInfo:
    def generate_filename(self, prefix: Literal['sg', 'fg', 'dg'] = 'sg', staff_ghost=False) -> str:
        # Refer to the following link for the full breakdown of the filename structures:
        # https://github.com/Dinostraw/MK8Leaderboards/wiki/Ghost-Data-(Deluxe)#filename-formats
        if prefix not in ('sg', 'fg', 'dg'):
            raise ValueError("Prefix must either be 'sg', 'fg', or 'dg'")

        # Ghosts created in-game have very short filenames
        if not staff_ghost:
            if prefix == 'dg':
                order = 0  # Can be anything from 0 to 31 inclusive
            elif self.track.id_ <= common.MK8Tracks.BIG_BLUE.id_:
                order = self.track.id_ - 0x10
            else:
                order = self.track.id_ - 0x1B
            return f"{prefix}{order:02d}.dat"

        # Staff ghosts have a much more complicated filename format
        # For the 48 base-game tracks (Big Blue has the highest ID of these)
        if self.track.id_ <= common.MK8Tracks.BIG_BLUE.id_:
            header = f"{prefix}{self.track.id_-0x10:02x}{self.track.id_:02x}"
        # For the DLC tracks
        else:
            header = f"{prefix}{self.track.id_-0x1B:02x}{self.track.id_:02x}"

        character = f"{self.character.value:02x}{self.variant:02x}{self.mii_weight:02x}"
        combo = f"{character}{self.vehicle_body.value:02x}{self.tire.value:02x}{self.glider.value:02x}"

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
        country = f"{self.country_id:04x}"
        motion = f"{int(self.motion):02x}0000"

        return header + combo + endtime + splits + name + country + motion + ".dat"

    def __init__(self, data: bytes, motion=False, lang: str = "en"):
        # Ghost data in Mario Kart 8 Deluxe follows a Little-Endian format
        data = bytes(data)
        data = data[0x48:] if data[0x0:0x4].decode('utf8') == "0GTC" else data
        if data[0x0:0x8] != b'\x00\x0C\x00\x00\x00\x00\x20\x00':
            raise InvalidGhostFormat(
                "Ghost not in the proper format: likely not a Mario Kart 8 Deluxe ghost"
            )

        # Basic Info
        if data[0x1CC] <= common.MK8Tracks.BIG_BLUE.id_:
            self.track = common.MK8Tracks(data[0x1CC])
        else:
            self.track = common.BoosterTracks(data[0x1CC])
        mode = data[0x3C]
        if mode == 2:
            self.mode = "150cc"
        elif mode == 3:
            self.mode = "200cc"
        else:
            self.mode = "???"
        self.motion = motion  # Still being investigated if this exists internally
        self.player_name_bytes = data[0x254:0x268]
        # Strip everything after the null character if one occurs
        self.player_name = self.player_name_bytes.decode("utf_16").split("\0", 1)[0]
        self.mii = MiiDataSwitch.parse(data[0x244:0x29C])

        # Timestamp
        self.year = int.from_bytes(data[0x0C:0x10], "little")
        self.month = data[0x10]
        self.day = data[0x14]
        self.weekday = common.Weekdays(data[0x18])
        self.hour = data[0x1C]
        self.min = data[0x20]
        self.sec = data[0x24]

        # Country Info
        self.country_id = int.from_bytes(data[0x2A0:0x2A2], "little")

        # Combo Info
        self.character = common.Characters(data[0x68])
        self.variant = data[0x6C]
        self.mii_weight = data[0x6D]
        self.vehicle_body = common.MK8DXVehicleBodies(data[0x5C])
        self.tire = common.Tires(data[0x60])
        self.glider = common.Gliders(data[0x64])

        # Total Time and Splits
        self.total_time = MK8TimeTuple(data[0x384], data[0x385], int.from_bytes(data[0x386:0x388], "little"))

        lap_offsets = [0x334, 0x33C, 0x344, 0x34C, 0x354, 0x35C, 0x364]
        if self.track != common.MK8Tracks.GCN_BABY_PARK:
            lap_offsets = lap_offsets[:3]

        self.lap_times = [MK8TimeTuple(data[x], data[x+1], int.from_bytes(data[x+2:x+4], "little"))
                          for x in lap_offsets]

    def __str__(self):
        return (
            f"Track: {self.track.fullname}\n"
            f"Mode: {self.mode}\n"
            f"Total Time: {self.total_time}\n"
            f"Lap times: {' | '.join(str(time) for time in self.lap_times)}\n"
            f"Motion Controls: {self.motion}\n"
            f"\n"
            f"Name: {self.player_name}\n"
            f"Country: {self.country_id:04X}\n"
            f"Timestamp: {str(self.weekday.name).title()}, "
            f"{self.year}-{self.month:02d}-{self.day:02d}, "
            f"{self.hour:02d}:{self.min:02d}:{self.sec:02d}\n"
            f"\n"
            f"Character: {str(self.character.name).replace('_', ' ').title()}\n"
            f"Variant: {self.variant}\n"
            f"Mii Weight Class: {self.mii_weight}\n"
            f"Combo: {str(self.vehicle_body.name).replace('_', ' ').title()}, "
            f"{str(self.tire.name).replace('_', ' ').title()}, "
            f"{str(self.glider.name).replace('_', ' ').title()}"
        )


def main():
    files = glob("../../Output/Ghosts (Deluxe)/*.dat")  # Ghost file(s)
    for file in files:
        with open(file, 'rb') as f:
            data = f.read()
        filename = re.split(r'[/\\]', file)[-1]
        if filename[:2] not in ('sg', 'fg', 'dg'):
            continue
        info = MK8DXGhostInfo(data, motion=filename[96:98] != '00')
        print("Original:  " + filename)
        print("Generated: " + info.generate_filename(filename[:2]))
        print(f"{info}\nhttps://studio.mii.nintendo.com/miis/image.png?data="
              f"{''.join(f'{x:02x}' for x in info.mii.to_studio_api())}"
              f"&width=512&type=face",
              end="\n\n==================\n\n")


if __name__ == "__main__":
    main()
