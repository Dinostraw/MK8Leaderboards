import os
import re
from glob import glob
from typing import NamedTuple

from mariokart8.mk8 import MK8Tracks as Tracks


class InvalidGhostFormat(Exception):
    pass


class MK8TimeTuple(NamedTuple):
    mins: int
    secs: int
    msecs: int

    def __str__(self):
        return f"{self.mins}:{self.secs:02}.{self.msecs:03}"


class MK8PlayerInfo:
    countries = {
        # Unknown:
        0: "???",

        # Japan:
        1: "JPN",

        # Americas:
        8:  "AIA", 9:  "ATG", 10: "ARG", 11: "ABW", 12: "BHS", 13: "BRB", 14: "BLZ", 15: "BOL",
        16: "BRA", 17: "VGB", 18: "CAN", 19: "CYM", 20: "CHL", 21: "COL", 22: "CRI", 23: "DMA",
        24: "DOM", 25: "ECU", 26: "SLV", 27: "GUF", 28: "GRD", 29: "GLP", 30: "GTM", 31: "GUY",
        32: "HTI", 33: "HND", 34: "JAM", 35: "MTQ", 36: "MEX", 37: "MSR", 38: "ANT", 39: "NIC",
        40: "PAN", 41: "PRY", 42: "PER", 43: "KNA", 44: "LCA", 45: "VCT", 46: "SUR", 47: "TTO",
        48: "TCA", 49: "USA", 50: "URY", 51: "VIR", 52: "VEN",

        # Europe, Africa, & Oceania:
        64:  "ALB", 65:  "AUS", 66:  "AUT", 67:  "BEL", 68:  "BIH", 69:  "BWA", 70:  "BGR",
        71:  "HRV", 72:  "CYP", 73:  "CZE", 74:  "DNK", 75:  "EST", 76:  "FIN", 77:  "FRA",
        78:  "DEU", 79:  "GRC", 80:  "HUN", 81:  "ISL", 82:  "IRL", 83:  "ITA", 84:  "LVA",
        85:  "LSO", 86:  "LIE", 87:  "LTU", 88:  "LUX", 89:  "MKD", 90:  "MLT", 91:  "MNE",
        92:  "MOZ", 93:  "NAM", 94:  "NLD", 95:  "NZL", 96:  "NOR", 97:  "POL", 98:  "PRT",
        99:  "ROU", 100: "RUS", 101: "SRB", 102: "SVK", 103: "SVN", 104: "ZAF", 105: "ESP",
        106: "SWZ", 107: "SWE", 108: "CHE", 109: "TUR", 110: "GBR", 111: "ZMB", 112: "ZWE",
        113: "AZE", 114: "MRT", 115: "MLI", 116: "NER", 117: "TCD", 118: "SDN", 119: "ERI",
        120: "DJI", 121: "SOM",

        # Southeast Asia:
        128: "TWN", 136: "KOR", 144: "HKG", 145: "MAC", 152: "IDN", 153: "SGP", 154: "THA",
        155: "PHL", 156: "MYS", 160: "CHN",

        # Middle East:
        168: "ARE", 169: "IND", 170: "EGY", 171: "OMN", 172: "QAT", 173: "KWT", 174: "SAU",
        175: "SYR", 176: "BHR", 177: "JOR"
    }

    def __init__(self, common_data):
        self.country_id = common_data[0x74]
        self.country = MK8PlayerInfo.countries[self.country_id]
        self.region_id = common_data[0x75]
        self.mii_name = common_data[0x2E:0x42].decode("utf_16")
        self.mii_name = self.mii_name.split("\0", 1)[0]

    def __str__(self):
        return ''.join(f"{k}: {v}\n" for k, v in self.__dict__.items())


class MK8GhostInfo:
    driver_dict = {0x00: "Mario", 0x01: "Luigi", 0x04: "Yoshi", 0x07: "Koopa Troopa",
                   0x08: "Bowser", 0x0A: "Wario", 0x0F: "Lakitu", 0x1C: "Morton",
                   0x1D: "Mii", 0x1F: "Link", 0x20: "Male Villager", 0x23: "Dry Bowser"}

    body_dict = {0x00: "Standard Kart", 0x01: "Pipe Frame", 0x02: "Mach 8", 0x03: "Steel Driver",
                 0x04: "Cat Cruiser", 0x05: "Circuit Special", 0x06: "Tri-Speeder", 0x07: "Badwagon",
                 0x08: "Prancer", 0x09: "Biddybuggy", 0x0A: "Landship", 0x0B: "Sneeker",
                 0x0C: "Sports Coupe", 0x0D: "Gold Standard", 0x13: "Varmint", 0x1D: "Blue Falcon",
                 0x1E: "Tanooki Kart", 0x20: "Master Cycle", 0x23: "Streetle"}

    tire_dict = {0x00: "Standard", 0x01: "Monster", 0x02: "Roller", 0x03: "Slim",
                 0x04: "Slick", 0x05: "Metal", 0x06: "Button", 0x07: "Off Road",
                 0x08: "Sponge", 0x09: "Wood", 0x0A: "Cushion", 0x0B: "Blue Standard",
                 0x0C: "Hot Monster", 0x0D: "Azure Roller", 0x0E: "Crimson Slim", 0x0F: "Cyber Slick",
                 0x10: "Retro Off Road", 0x11: "Gold Tires", 0x12: "Gla Tires", 0x13: "Triforce Tires",
                 0x14: "Leaf Tires"}

    glider_dict = {0x00: "Super Glider", 0x01: "Cloud Glider", 0x02: "Wario Wing", 0x03: "Waddle Wing",
                   0x04: "Peach Parasol", 0x05: "Parachute", 0x06: "Parafoil", 0x07: "Flower Glider",
                   0x08: "Bowser Kite", 0x09: "Plane Glider", 0x0A: "MKTV Parafoil", 0x0B: "Gold Glider",
                   0x0C: "Hylian Kite", 0x0D: "Paper Glider"}

    def generate_filename(self, prefix='dg'):
        # Based on the information gathered in this forum post:
        # https://gbatemp.net/threads/post-your-wiiu-cheat-codes-here.395443/post-8640417
        if prefix == 'dg':
            header = f"{prefix}00{self.track:02x}"
        else:
            header = f"{prefix}{self.track-0x10:02x}{self.track:02x}"

        combo = f"{self.character:02x}0000{self.vehicle_body:02x}{self.tire:02x}{self.glider:02x}"

        endtime = f'{self.total_time.mins:01x}{self.total_time.secs:02x}{self.total_time.msecs:03x}'

        if self.track == Tracks.GCN_BABY_PARK.id_:
            splits_pt1 = ''.join([f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times[:5]])
            splits_pt2 = ''.join([f'{t.mins:01x}{t.secs:02x}{t.msecs:03x}' for t in self.lap_times[5:]])
        else:
            splits_pt2 = "93b3e7" * 2  # Two filler splits, each represents a time of 9:59.999
            splits_pt1 = "%s%s" % (''.join(f"{t.mins:01x}{t.secs:02x}{t.msecs:03x}" for t in self.lap_times[:3]),
                                   splits_pt2)  # Since most tracks have just 3 laps, append filler
        mii = ''.join(f"{b:02x}" for b in self.mii_name_bytes)
        country = f"{self.country:02x}000000"

        return header + combo + endtime + splits_pt1 + mii + country + splits_pt2 + ".dat"

    def __init__(self, data):
        data = bytes(data)
        data = data[0x48:] if data[0x0:0x4].decode('utf8') == "CTG0" else data

        if data[0x0:0x6] != b'\x00\x00\x04\x00\x03\xa0':
            raise InvalidGhostFormat("Ghost not in the proper format: likely not an mariokart8 ghost")

        # Basic Info
        self.track = data[0x17F]
        self.motion = True if data[0x2B3] == 0 else False  # Originally though 0x2B3 was the offset
        self.mii_name_bytes = data[0x304:0x318]
        self.mii_name = self.mii_name_bytes.decode("utf_16_be")  # Force byte order

        # Timestamp
        self.year = int.from_bytes(data[0x0E:0x10], "big")
        self.month = data[0x13]
        self.day = data[0x17]

        # Location Info
        self.country = data[0x2A4]
        self.subdivision = data[0x2A5]

        # Combo Info
        self.character = data[0x3B]
        self.vehicle_body = data[0x2F]
        self.tire = data[0x33]
        self.glider = data[0x37]

        # Total Time and Splits
        self.total_time = MK8TimeTuple(data[0x36D], data[0x36E], int.from_bytes(data[0x370:0x372], "big"))

        lap_offsets = [0x331, 0x33D, 0x349, 0x355, 0x361, 0x385, 0x391]
        if self.track != Tracks.GCN_BABY_PARK.id_:
            lap_offsets = lap_offsets[0:3]

        self.lap_times = [MK8TimeTuple(data[x], data[x+1], int.from_bytes(data[x+3:x+5], "big"))
                          for x in lap_offsets]

    def __str__(self):
        return ''.join(f"{k}: {v}\n" for k, v in self.__dict__.items())


def main():
    files = glob("../Samples/Output/Ghosts/*.dat")
    for file in files:
        with open(file, 'rb') as f:
            data = f.read()
        info = MK8GhostInfo(data)
        print("Original:  " + re.split(r'[/\\]', file)[-1])
        print("Generated: " + info.generate_filename())
        print(info, end="\n\n")


if __name__ == "__main__":
    main()
