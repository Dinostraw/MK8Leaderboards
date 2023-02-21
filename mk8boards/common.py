import json
import os
from enum import Enum, EnumMeta
from typing import NamedTuple

from mk8boards.str_mappings import standardize_abbr


def _initialize_aliases():
    with open(os.path.join(os.path.dirname(__file__), "track_abbr.json"), encoding="utf-8") as f:
        return {standardize_abbr(abbr): track
                for track, abbrs in json.load(f).items()
                for abbr in abbrs}


class MK8GameInfo:
    TITLE_ID_EUR = 0x000500001010ED00
    TITLE_ID_USA = 0x000500001010EC00
    TITLE_ID_JAP = 0x000500001010EB00
    LATEST_VERSION = 64

    GAME_SERVER_ID = 0x1010EB00
    ACCESS_KEY = "25dbf96a"
    NEX_VERSION = 30504  # 3.5.4 (AMK patch)


class MK8DXGameInfo:
    TITLE_ID = 0x0100152000022000
    LATEST_VERSION = 0xA0000

    GAME_SERVER_ID = 0x2B309E01
    ACCESS_KEY = "09c1c475"
    NEX_VERSION = 40302


class InvalidGhostFormat(Exception):
    pass


class MK8TimeTuple(NamedTuple):
    mins: int
    secs: int
    msecs: int

    def __str__(self):
        return f"{self.mins}:{self.secs:02}.{self.msecs:03}"


class _TrackEnumMeta(EnumMeta):
    _abbr_aliases = _initialize_aliases()

    def __getitem__(self, name):
        if standardize_abbr(name) in self._abbr_aliases:
            return super().__getitem__(self._abbr_aliases[standardize_abbr(name)])
        return super().__getitem__(name)


class _Tracks(Enum, metaclass=_TrackEnumMeta):
    # https://stackoverflow.com/a/43210118
    def __new__(cls, *values):
        obj = object.__new__(cls)
        # ID value is the canonical value
        obj._value_ = values[-1]
        for other_value in values[:-1]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __init__(self, fullname: str, abbr: str, id_: int):
        self.fullname = fullname
        self.abbr = abbr
        self.id_ = id_


# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
class MK8Tracks(_Tracks):
    # Nitro Tracks
    MARIO_KART_STADIUM = ("Mario Kart Stadium", "MKS", 27)
    WATER_PARK = ("Water Park", "WP", 28)
    SWEET_SWEET_CANYON = ("Sweet Sweet Canyon", "SSC", 19)
    THWOMP_RUINS = ("Thwomp Ruins", "TR", 17)

    MARIO_CIRCUIT = ("Mario Circuit", "MC", 16)
    TOAD_HARBOR = ("Toad Harbor", "TH", 18)
    TWISTED_MANSION = ("Twisted Mansion", "TM", 20)
    SHY_GUY_FALLS = ("Shy Guy Falls", "SGF", 21)

    SUNSHINE_AIRPORT = ("Sunshine Airport", "SA", 26)
    DOLPHIN_SHOALS = ("Dolphin Shoals", "DS", 29)
    ELECTRODROME = ("Electrodrome", "Ed", 25)
    MOUNT_WARIO = ("Mount Wario", "MW", 24)

    CLOUDTOP_CRUISE = ("Cloudtop Cruise", "CC", 23)
    BONE_DRY_DUNES = ("Bone-Dry Dunes", "BDD", 22)
    BOWSER_CASTLE = ("Bowser's Castle", "BC", 30)
    RAINBOW_ROAD = ("Rainbow Road", "RR", 31)

    # Retro Tracks
    WII_MOO_MOO_MEADOWS = ("Wii Moo Moo Meadows", "rMMM", 33)
    GBA_MARIO_CIRCUIT = ("GBA Mario Circuit", "rMC", 38)
    DS_CHEEP_CHEEP_BEACH = ("DS Cheep Cheep Beach", "rCCB", 36)
    N64_TOAD_TURNPIKE = ("N64 Toad's Turnpike", "rTT", 35)

    GCN_DRY_DRY_DESERT = ("GCN Dry Dry Desert", "rDDD", 42)
    SNES_DONUT_PLAINS_3 = ("SNES Donut Plains 3", "rDP3", 41)
    N64_ROYAL_RACEWAY = ("N64 Royal Raceway", "rRRy", 34)
    MK7_DK_JUNGLE = ("3DS DK Jungle", "rDKJ", 32)

    DS_WARIO_STADIUM = ("DS Wario Stadium", "rWS", 46)
    GCN_SHERBET_LAND = ("GCN Sherbet Land", "rSL", 37)
    MK7_MUSIC_PARK = ("3DS Music Park", "rMP", 39)
    N64_YOSHI_VALLEY = ("N64 Yoshi Valley", "rYV", 45)

    DS_TICK_TOCK_CLOCK = ("DS Tick-Tock Clock", "rTTC", 44)
    MK7_PIRANHA_PLANT_SLIDE = ("3DS Piranha Plant Slide", "rPPS", 43)
    WII_GRUMBLE_VOLCANO = ("Wii Grumble Volcano", "rGV", 40)
    N64_RAINBOW_ROAD = ("N64 Rainbow Road", "rRRd", 47)

    # DLC Pack 1 Tracks
    GCN_YOSHI_CIRCUIT = ("GCN Yoshi Circuit", "dYC", 56)
    EXCITEBIKE_ARENA = ("Excitebike Arena", "dEA", 53)
    DRAGON_DRIFTWAY = ("Dragon Driftway", "dDD", 50)
    MUTE_CITY = ("Mute City", "dMC", 49)

    WII_WARIO_GOLD_MINE = ("Wii Wario's Gold Mine", "dWGM", 57)
    SNES_RAINBOW_ROAD = ("SNES Rainbow Road", "dRR", 58)
    ICE_ICE_OUTPOST = ("Ice Ice Outpost", "dIIO", 55)
    HYRULE_CIRCUIT = ("Hyrule Circuit", "dHC", 51)

    # DLC Pack 2 Tracks
    GCN_BABY_PARK = ("GCN Baby Park", "dBP", 61)
    GBA_CHEESE_LAND = ("GBA Cheese Land", "dCL", 62)
    WILD_WOODS = ("Wild Woods", "dWW", 54)
    ANIMAL_CROSSING = ("Animal Crossing", "dAC", 52)

    MK7_NEO_BOWSER_CITY = ("3DS Neo Bowser City", "dNBC", 60)
    GBA_RIBBON_ROAD = ("GBA Ribbon Road", "dRiR", 59)
    SUPER_BELL_SUBWAY = ("Super Bell Subway", "dSBS", 48)
    BIG_BLUE = ("Big Blue", "dBB", 63)


# Booster DLC Track IDs: https://github.com/Dinostraw/MK8Leaderboards/wiki/Booster-Track-IDs
class BoosterTracks(_Tracks):
    # Wave 1 Tracks
    TOUR_PARIS_PROMENADE = ("Tour Paris Promenade", "bPP", 75)
    MK7_TOAD_CIRCUIT = ("3DS Toad Circuit", "bTC", 76)
    N64_CHOCO_MOUNTAIN = ("N64 Choco Mountain", "bCMo", 77)
    WII_COCONUT_MALL = ("Wii Coconut Mall", "bCMa", 78)

    TOUR_TOKYO_BLUR = ("Tour Tokyo Blur", "bTB", 79)
    DS_SHROOM_RIDGE = ("DS Shroom Ridge", "bSR", 80)
    GBA_SKY_GARDEN = ("GBA Sky Garden", "bSG", 81)
    TOUR_NINJA_HIDEAWAY = ("Tour Ninja Hideaway", "bNH", 82)

    # Wave 2 Tracks
    TOUR_NEW_YORK_MINUTE = ("Tour New York Minute", "bNYM", 83)
    SNES_MARIO_CIRCUIT_3 = ("SNES Mario Circuit 3", "bMC3", 84)
    N64_KALIMARI_DESERT = ("N64 Kalimari Desert", "bKD", 85)
    DS_WALUIGI_PINBALL = ("DS Waluigi Pinball", "bWP", 86)

    TOUR_SYDNEY_SPRINT = ("Tour Sydney Sprint", "bSS", 87)
    GBA_SNOW_LAND = ("GBA Snow Land", "bSL", 88)
    WII_MUSHROOM_GORGE = ("Wii Mushroom Gorge", "bMG", 89)
    SKY_HIGH_SUNDAE = ("Sky-High Sundae", "bSHS", 90)

    # Wave 3 Tracks
    TOUR_LONDON_LOOP = ("Tour London Loop", "bLL", 91)
    GBA_BOO_LAKE = ("GBA Boo Lake", "bBL", 92)
    MK7_ROCK_ROCK_MOUNTAIN = ("3DS Rock Rock Mountain", "bRRM", 93)
    WII_MAPLE_TREEWAY = ("Wii Maple Treeway", "bMT", 94)

    TOUR_BERLIN_BYWAYS = ("Tour Berlin Byways", "bBB", 95)
    DS_PEACH_GARDENS = ("DS Peach Gardens", "bPG", 96)
    TOUR_MERRY_MOUNTAIN = ("Tour Merry Mountain", "bMM", 97)
    MK7_RAINBOW_ROAD = ("3DS Rainbow Road", "bRR", 98)


class _Cups(Enum):
    # https://stackoverflow.com/a/43210118
    def __new__(cls, *values):
        obj = object.__new__(cls)
        obj._value_ = values
        for x in values:
            cls._value2member_map_[x] = obj
        return obj

    def __init__(self, track0: MK8Tracks, track1: MK8Tracks, track2: MK8Tracks, track3: MK8Tracks):
        self.track0 = track0
        self.track1 = track1
        self.track2 = track2
        self.track3 = track3


# Found across both version of the game; each cup has 4 predefined courses
class MK8Cups(_Cups):
    # Nitro Cups
    MUSHROOM = (MK8Tracks.MARIO_KART_STADIUM, MK8Tracks.WATER_PARK,
                MK8Tracks.SWEET_SWEET_CANYON, MK8Tracks.THWOMP_RUINS)
    FLOWER = (MK8Tracks.MARIO_CIRCUIT, MK8Tracks.TOAD_HARBOR,
              MK8Tracks.TWISTED_MANSION, MK8Tracks.SHY_GUY_FALLS)
    STAR = (MK8Tracks.SUNSHINE_AIRPORT, MK8Tracks.DOLPHIN_SHOALS,
            MK8Tracks.ELECTRODROME, MK8Tracks.MOUNT_WARIO)
    SPECIAL = (MK8Tracks.CLOUDTOP_CRUISE, MK8Tracks.BONE_DRY_DUNES,
               MK8Tracks.BOWSER_CASTLE, MK8Tracks.RAINBOW_ROAD)

    # Retro Cups
    SHELL = (MK8Tracks.WII_MOO_MOO_MEADOWS, MK8Tracks.GBA_MARIO_CIRCUIT,
             MK8Tracks.DS_CHEEP_CHEEP_BEACH, MK8Tracks.N64_TOAD_TURNPIKE)
    BANANA = (MK8Tracks.GCN_DRY_DRY_DESERT, MK8Tracks.SNES_DONUT_PLAINS_3,
              MK8Tracks.N64_ROYAL_RACEWAY, MK8Tracks.MK7_DK_JUNGLE)
    LEAF = (MK8Tracks.DS_WARIO_STADIUM, MK8Tracks.GCN_SHERBET_LAND,
            MK8Tracks.MK7_MUSIC_PARK, MK8Tracks.N64_YOSHI_VALLEY)
    LIGHTNING = (MK8Tracks.DS_TICK_TOCK_CLOCK, MK8Tracks.MK7_PIRANHA_PLANT_SLIDE,
                 MK8Tracks.WII_GRUMBLE_VOLCANO, MK8Tracks.N64_RAINBOW_ROAD)

    # DLC Cups
    EGG = (MK8Tracks.GCN_YOSHI_CIRCUIT, MK8Tracks.EXCITEBIKE_ARENA,
           MK8Tracks.DRAGON_DRIFTWAY, MK8Tracks.MUTE_CITY)
    TRIFORCE = (MK8Tracks.WII_WARIO_GOLD_MINE, MK8Tracks.SNES_RAINBOW_ROAD,
                MK8Tracks.ICE_ICE_OUTPOST, MK8Tracks.HYRULE_CIRCUIT)
    CROSSING = (MK8Tracks.GCN_BABY_PARK, MK8Tracks.GBA_CHEESE_LAND,
                MK8Tracks.WILD_WOODS, MK8Tracks.ANIMAL_CROSSING)
    BELL = (MK8Tracks.MK7_NEO_BOWSER_CITY, MK8Tracks.GBA_RIBBON_ROAD,
            MK8Tracks.SUPER_BELL_SUBWAY, MK8Tracks.BIG_BLUE)


# Exclusive to Deluxe; each cup has 4 predefined courses
class BoosterCups(_Cups):
    # Wave 1 Cups
    GOLDEN_DASH = (BoosterTracks.TOUR_PARIS_PROMENADE, BoosterTracks.MK7_TOAD_CIRCUIT,
                   BoosterTracks.N64_CHOCO_MOUNTAIN, BoosterTracks.WII_COCONUT_MALL)
    LUCKY_CAT = (BoosterTracks.TOUR_TOKYO_BLUR, BoosterTracks.DS_SHROOM_RIDGE,
                 BoosterTracks.GBA_SKY_GARDEN, BoosterTracks.TOUR_NINJA_HIDEAWAY)

    # Wave 2 Cups
    TURNIP = (BoosterTracks.TOUR_NEW_YORK_MINUTE, BoosterTracks.SNES_MARIO_CIRCUIT_3,
              BoosterTracks.N64_KALIMARI_DESERT, BoosterTracks.DS_WALUIGI_PINBALL)
    PROPELLER = (BoosterTracks.TOUR_SYDNEY_SPRINT, BoosterTracks.GBA_SNOW_LAND,
                 BoosterTracks.WII_MUSHROOM_GORGE, BoosterTracks.SKY_HIGH_SUNDAE)

    # Wave 3 Cups
    ROCK = (BoosterTracks.TOUR_LONDON_LOOP, BoosterTracks.GBA_BOO_LAKE,
            BoosterTracks.MK7_ROCK_ROCK_MOUNTAIN, BoosterTracks.WII_MAPLE_TREEWAY)
    MOON = (BoosterTracks.TOUR_BERLIN_BYWAYS, BoosterTracks.DS_PEACH_GARDENS,
            BoosterTracks.TOUR_MERRY_MOUNTAIN, BoosterTracks.MK7_RAINBOW_ROAD)


class Characters(Enum):
    MARIO = 0x00
    LUIGI = 0x01
    PEACH = 0x02
    DAISY = 0x03
    YOSHI = 0x04
    TOAD = 0x05
    TOADETTE = 0x06
    KOOPA_TROOPA = 0x07
    BOWSER = 0x08
    DONKEY_KONG = 0x09
    WARIO = 0x0A
    WALUIGI = 0x0B
    ROSALINA = 0x0C
    METAL_MARIO = 0x0D
    PINK_GOLD_PEACH = 0x0E
    LAKITU = 0x0F
    SHY_GUY = 0x10
    BABY_MARIO = 0x11
    BABY_LUIGI = 0x12
    BABY_PEACH = 0x13
    BABY_DAISY = 0x14
    BABY_ROSALINA = 0x15
    LARRY = 0x16
    LEMMY = 0x17
    WENDY = 0x18
    LUDWIG = 0x19
    IGGY = 0x1A
    ROY = 0x1B
    MORTON = 0x1C
    MII = 0x1D

    # Wii U DLC (Included in Deluxe Base-Game)
    TANOOKI_MARIO = 0x1E
    LINK = 0x1F
    MALE_VILLAGER = 0x20
    ISABELLE = 0x21
    CAT_PEACH = 0x22
    DRY_BOWSER = 0x23
    FEMALE_VILLAGER = 0x24

    # Deluxe Exclusive
    GOLD_MARIO = 0x25
    DRY_BONES = 0x26
    BOWSER_JR = 0x27
    KING_BOO = 0x28
    INKLING_GIRL = 0x29
    INKLING_BOY = 0x2A
    CHAMPION_LINK = 0x2B


class MK8VehicleBodies(Enum):
    # Base-Game
    STANDARD_KART = 0x00
    PIPE_FRAME = 0x01
    MACH_8 = 0x02
    STEEL_DRIVER = 0x03
    CAT_CRUISER = 0x04
    CIRCUIT_SPECIAL = 0x05
    TRI_SPEEDER = 0x06
    BADWAGON = 0x07
    PRANCER = 0x08
    BIDDYBUGGY = 0x09
    LANDSHIP = 0x0A
    SNEEKER = 0x0B
    SPORTS_COUPE = 0x0C
    GOLD_STANDARD = 0x0D
    STANDARD_BIKE = 0x0E
    COMET = 0x0F
    SPORT_BIKE = 0x10
    THE_DUKE = 0x11
    FLAME_RIDER = 0x12
    VARMINT = 0x13
    MR_SCOOTY = 0x14
    JET_BIKE = 0x15
    YOSHI_BIKE = 0x16
    STANDARD_ATV = 0x17
    WILD_WIGGLER = 0x18
    TEDDY_BUGGY = 0x19

    # Mercedes DLC
    GLA = 0x1A
    W_25_SILVER_ARROW = 0x1B
    SL_ROADSTER = 0x1C

    # DLC Pack 1
    BLUE_FALCON = 0x1D
    TANOOKI_KART = 0x1E
    B_DASHER = 0x1F
    MASTER_CYCLE = 0x20

    # DLC Pack 2
    STREETLE = 0x23
    P_WING = 0x24
    CITY_TRIPPER = 0x25
    BONE_RATTLER = 0x26


# Separate class from MK8VehicleBodies since the ID gap that occurs in between
# Master Cycle and Streetle was closed on Deluxe by altering the ID values for
# Streetle, P Wing, City Tripper, and Bone Rattler
class MK8DXVehicleBodies(Enum):
    STANDARD_KART = 0x00
    PIPE_FRAME = 0x01
    MACH_8 = 0x02
    STEEL_DRIVER = 0x03
    CAT_CRUISER = 0x04
    CIRCUIT_SPECIAL = 0x05
    TRI_SPEEDER = 0x06
    BADWAGON = 0x07
    PRANCER = 0x08
    BIDDYBUGGY = 0x09
    LANDSHIP = 0x0A
    SNEEKER = 0x0B
    SPORTS_COUPE = 0x0C
    GOLD_STANDARD = 0x0D
    STANDARD_BIKE = 0x0E
    COMET = 0x0F
    SPORT_BIKE = 0x10
    THE_DUKE = 0x11
    FLAME_RIDER = 0x12
    VARMINT = 0x13
    MR_SCOOTY = 0x14
    JET_BIKE = 0x15
    YOSHI_BIKE = 0x16
    STANDARD_ATV = 0x17
    WILD_WIGGLER = 0x18
    TEDDY_BUGGY = 0x19
    GLA = 0x1A
    W_25_SILVER_ARROW = 0x1B
    SL_ROADSTER = 0x1C
    BLUE_FALCON = 0x1D
    TANOOKI_KART = 0x1E
    B_DASHER = 0x1F
    MASTER_CYCLE = 0x20
    STREETLE = 0x21
    P_WING = 0x22
    CITY_TRIPPER = 0x23
    BONE_RATTLER = 0x24
    KOOPA_CLOWN = 0x25
    SPLAT_BUGGY = 0x26
    INKSTRIKER = 0x27
    MASTER_CYCLE_ZERO = 0x28


class Tires(Enum):
    STANDARD = 0x00
    MONSTER = 0x01
    ROLLER = 0x02
    SLIM = 0x03
    SLICK = 0x04
    METAL = 0x05
    BUTTON = 0x06
    OFF_ROAD = 0x07
    SPONGE = 0x08
    WOOD = 0x09
    CUSHION = 0x0A
    BLUE_STANDARD = 0x0B
    HOT_MONSTER = 0x0C
    AZURE_ROLLER = 0x0D
    CRIMSON_SLIM = 0x0E
    CYBER_SLICK = 0x0F
    RETRO_OFF_ROAD = 0x10
    GOLD_TIRES = 0x11
    GLA_TIRES = 0x12
    TRIFORCE_TIRES = 0x13
    LEAF_TIRES = 0x14
    ANCIENT_TIRES = 0x15


class Gliders(Enum):
    SUPER_GLIDER = 0x00
    CLOUD_GLIDER = 0x01
    WARIO_WING = 0x02
    WADDLE_WING = 0x03
    PEACH_PARASOL = 0x04
    PARACHUTE = 0x05
    PARAFOIL = 0x06
    FLOWER_GLIDER = 0x07
    BOWSER_KITE = 0x08
    PLANE_GLIDER = 0x09
    MKTV_PARAFOIL = 0x0A
    GOLD_GLIDER = 0x0B
    HYLIAN_KITE = 0x0C
    PAPER_GLIDER = 0x0D
    PARAGLIDER = 0x0E


class Weekdays(Enum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
