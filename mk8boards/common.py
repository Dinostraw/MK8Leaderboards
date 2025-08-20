import json
import os
from enum import Enum, EnumMeta, IntEnum
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
    LATEST_VERSION = 128  # 4.2 (RCE patch)

    GAME_SERVER_ID = 0x1010EB00
    ACCESS_KEY = "25dbf96a"
    NEX_VERSION = 30504  # 3.5.4 (AMK patch)


class MK8DXGameInfo:
    TITLE_ID = 0x0100152000022000
    LATEST_VERSION = 0x150000  # 3.0.5

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


class _Tracks(IntEnum, metaclass=_TrackEnumMeta):
    # https://stackoverflow.com/a/43210118
    def __new__(cls, *values):
        obj = int.__new__(cls, values[0])
        # First value is the canonical value
        obj._value_ = values[0]
        for other_value in values[1:]:
            cls._value2member_map_[other_value] = obj
        obj._all_values = values
        return obj

    def __init__(self, id_: int, fullname: str, abbr: str):
        self._value_ = id_
        self.fullname = fullname
        self.abbr = abbr


# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
class MK8Tracks(_Tracks):
    # Nitro Tracks
    MARIO_KART_STADIUM = (27, "Mario Kart Stadium", "MKS")
    WATER_PARK = (28, "Water Park", "WP")
    SWEET_SWEET_CANYON = (19, "Sweet Sweet Canyon", "SSC")
    THWOMP_RUINS = (17, "Thwomp Ruins", "TR")

    MARIO_CIRCUIT = (16, "Mario Circuit", "MC")
    TOAD_HARBOR = (18, "Toad Harbor", "TH")
    TWISTED_MANSION = (20, "Twisted Mansion", "TM")
    SHY_GUY_FALLS = (21, "Shy Guy Falls", "SGF")

    SUNSHINE_AIRPORT = (26, "Sunshine Airport", "SA")
    DOLPHIN_SHOALS = (29, "Dolphin Shoals", "DS")
    ELECTRODROME = (25, "Electrodrome", "Ed")
    MOUNT_WARIO = (24, "Mount Wario", "MW")

    CLOUDTOP_CRUISE = (23, "Cloudtop Cruise", "CC")
    BONE_DRY_DUNES = (22, "Bone-Dry Dunes", "BDD")
    BOWSER_CASTLE = (30, "Bowser's Castle", "BC")
    RAINBOW_ROAD = (31, "Rainbow Road", "RR")

    # Retro Tracks
    WII_MOO_MOO_MEADOWS = (33, "Wii Moo Moo Meadows", "rMMM")
    GBA_MARIO_CIRCUIT = (38, "GBA Mario Circuit", "rMC")
    DS_CHEEP_CHEEP_BEACH = (36, "DS Cheep Cheep Beach", "rCCB")
    N64_TOAD_TURNPIKE = (35, "N64 Toad's Turnpike", "rTT")

    GCN_DRY_DRY_DESERT = (42, "GCN Dry Dry Desert", "rDDD")
    SNES_DONUT_PLAINS_3 = (41, "SNES Donut Plains 3", "rDP3")
    N64_ROYAL_RACEWAY = (34, "N64 Royal Raceway", "rRRy")
    MK7_DK_JUNGLE = (32, "3DS DK Jungle", "rDKJ")

    DS_WARIO_STADIUM = (46, "DS Wario Stadium", "rWS")
    GCN_SHERBET_LAND = (37, "GCN Sherbet Land", "rSL")
    MK7_MUSIC_PARK = (39, "3DS Music Park", "rMP")
    N64_YOSHI_VALLEY = (45, "N64 Yoshi Valley", "rYV")

    DS_TICK_TOCK_CLOCK = (44, "DS Tick-Tock Clock", "rTTC")
    MK7_PIRANHA_PLANT_SLIDE = (43, "3DS Piranha Plant Slide", "rPPS")
    WII_GRUMBLE_VOLCANO = (40, "Wii Grumble Volcano", "rGV")
    N64_RAINBOW_ROAD = (47, "N64 Rainbow Road", "rRRd")

    # DLC Pack 1 Tracks
    GCN_YOSHI_CIRCUIT = (56, "GCN Yoshi Circuit", "dYC")
    EXCITEBIKE_ARENA = (53, "Excitebike Arena", "dEA")
    DRAGON_DRIFTWAY = (50, "Dragon Driftway", "dDD")
    MUTE_CITY = (49, "Mute City", "dMC")

    WII_WARIO_GOLD_MINE = (57, "Wii Wario's Gold Mine", "dWGM")
    SNES_RAINBOW_ROAD = (58, "SNES Rainbow Road", "dRR")
    ICE_ICE_OUTPOST = (55, "Ice Ice Outpost", "dIIO")
    HYRULE_CIRCUIT = (51, "Hyrule Circuit", "dHC")

    # DLC Pack 2 Tracks
    GCN_BABY_PARK = (61, "GCN Baby Park", "dBP")
    GBA_CHEESE_LAND = (62, "GBA Cheese Land", "dCL")
    WILD_WOODS = (54, "Wild Woods", "dWW")
    ANIMAL_CROSSING = (52, "Animal Crossing", "dAC")

    MK7_NEO_BOWSER_CITY = (60, "3DS Neo Bowser City", "dNBC")
    GBA_RIBBON_ROAD = (59, "GBA Ribbon Road", "dRiR")
    SUPER_BELL_SUBWAY = (48, "Super Bell Subway", "dSBS")
    BIG_BLUE = (63, "Big Blue", "dBB")

    # Variants: these tracks are inaccessible in Time Trials
    # ANIMAL_CROSSING_SPRING = (64, "Animal Crossing: Spring", "dACs")
    # ANIMAL_CROSSING_AUTUMN = (65, "Animal Crossing: Autumn", "dACa")
    # ANIMAL_CROSSING_WINTER = (66, "Animal Crossing: Winter", "dACw")


# Booster DLC Track IDs: https://github.com/Dinostraw/MK8Leaderboards/wiki/Booster-Track-IDs
class BoosterTracks(_Tracks):
    # Wave 1 Tracks
    TOUR_PARIS_PROMENADE = (75, "Tour Paris Promenade", "bPP")
    MK7_TOAD_CIRCUIT = (76, "3DS Toad Circuit", "bTC")
    N64_CHOCO_MOUNTAIN = (77, "N64 Choco Mountain", "bCMo")
    WII_COCONUT_MALL = (78, "Wii Coconut Mall", "bCMa")

    TOUR_TOKYO_BLUR = (79, "Tour Tokyo Blur", "bTB")
    DS_SHROOM_RIDGE = (80, "DS Shroom Ridge", "bSR")
    GBA_SKY_GARDEN = (81, "GBA Sky Garden", "bSG")
    TOUR_NINJA_HIDEAWAY = (82, "Tour Ninja Hideaway", "bNH")

    # Wave 2 Tracks
    TOUR_NEW_YORK_MINUTE = (83, "Tour New York Minute", "bNYM")
    SNES_MARIO_CIRCUIT_3 = (84, "SNES Mario Circuit 3", "bMC3")
    N64_KALIMARI_DESERT = (85, "N64 Kalimari Desert", "bKD")
    DS_WALUIGI_PINBALL = (86, "DS Waluigi Pinball", "bWP")

    TOUR_SYDNEY_SPRINT = (87, "Tour Sydney Sprint", "bSS")
    GBA_SNOW_LAND = (88, "GBA Snow Land", "bSL")
    WII_MUSHROOM_GORGE = (89, "Wii Mushroom Gorge", "bMG")
    SKY_HIGH_SUNDAE = (90, "Sky-High Sundae", "bSHS")

    # Wave 3 Tracks
    TOUR_LONDON_LOOP = (91, "Tour London Loop", "bLL")
    GBA_BOO_LAKE = (92, "GBA Boo Lake", "bBL")
    MK7_ROCK_ROCK_MOUNTAIN = (93, "3DS Rock Rock Mountain", "bRRM")
    WII_MAPLE_TREEWAY = (94, "Wii Maple Treeway", "bMT")

    TOUR_BERLIN_BYWAYS = (95, "Tour Berlin Byways", "bBB")
    DS_PEACH_GARDENS = (96, "DS Peach Gardens", "bPG")
    TOUR_MERRY_MOUNTAIN = (97, "Tour Merry Mountain", "bMM")
    MK7_RAINBOW_ROAD = (98, "3DS Rainbow Road", "bRR")

    # Wave 4 Tracks
    TOUR_AMSTERDAM_DRIFT = (99, "Tour Amsterdam Drift", "bAD")
    GBA_RIVERSIDE_PARK = (100, "GBA Riverside Park", "bRP")
    WII_DK_SUMMIT = (101, "Wii DK Summit", "bDKS")
    YOSHI_ISLAND = (102, "Yoshi's Island", "bYI")

    TOUR_BANGKOK_RUSH = (103, "Tour Bangkok Rush", "bBR")
    DS_MARIO_CIRCUIT = (104, "DS Mario Circuit", "bMC")
    GCN_WALUIGI_STADIUM = (105, "GCN Waluigi Stadium", "bWS")
    TOUR_SINGAPORE_SPEEDWAY = (106, "Tour Singapore Speedway", "bSSy")

    # Wave 5 Tracks
    TOUR_ATHENS_DASH = (107, "Tour Athens Dash", "bAtD")
    GCN_DAISY_CRUISER = (108, "GCN Daisy Cruiser", "bDC")
    WII_MOONVIEW_HIGHWAY = (109, "Wii Moonview Highway", "bMH")
    SQUEAKY_CLEAN_SPRINT = (110, "Squeaky Clean Sprint", "bSCS")

    TOUR_LOS_ANGELES_LAPS = (111, "Tour Los Angeles Laps", "bLAL")
    GBA_SUNSET_WILDS = (112, "GBA Sunset Wilds", "bSW")
    WII_KOOPA_CAPE = (113, "Wii Koopa Cape", "bKC")
    TOUR_VANCOUVER_VELOCITY = (114, "Tour Vancouver Velocity", "bVV")

    # Wave 6 Tracks
    TOUR_ROME_AVANTI = (115, "Tour Rome Avanti", "bRA")
    GCN_DK_MOUNTAIN = (116, "GCN DK Mountain", "bDKM")
    WII_DAISY_CIRCUIT = (117, "Wii Daisy Circuit", "bDCt")
    TOUR_PIRANHA_PLANT_COVE = (118, "Tour Piranha Plant Cove", "bPPC")

    TOUR_MADRID_DRIVE = (119, "Tour Madrid Drive", "bMD")
    MK7_ROSALINA_ICE_WORLD = (120, "3DS Rosalina's Ice World", "bRIW")
    SNES_BOWSER_CASTLE_3 = (121, "SNES Bowser Castle 3", "bBC3")
    WII_RAINBOW_ROAD = (122, "Wii Rainbow Road", "bRRw")


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


# Found across both versions of the game; each cup has 4 predefined courses
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

    # Wave 4 Cups
    FRUIT = (BoosterTracks.TOUR_AMSTERDAM_DRIFT, BoosterTracks.GBA_RIVERSIDE_PARK,
             BoosterTracks.WII_DK_SUMMIT, BoosterTracks.YOSHI_ISLAND)
    BOOMERANG = (BoosterTracks.TOUR_BANGKOK_RUSH, BoosterTracks.DS_MARIO_CIRCUIT,
                 BoosterTracks.GCN_WALUIGI_STADIUM, BoosterTracks.TOUR_SINGAPORE_SPEEDWAY)

    # Wave 5 Cups
    FEATHER = (BoosterTracks.TOUR_ATHENS_DASH, BoosterTracks.GCN_DAISY_CRUISER,
               BoosterTracks.WII_MOONVIEW_HIGHWAY, BoosterTracks.SQUEAKY_CLEAN_SPRINT)
    CHERRY = (BoosterTracks.TOUR_LOS_ANGELES_LAPS, BoosterTracks.GBA_SUNSET_WILDS,
              BoosterTracks.WII_KOOPA_CAPE, BoosterTracks.TOUR_VANCOUVER_VELOCITY)

    # Wave 6 Cups
    ACORN = (BoosterTracks.TOUR_ROME_AVANTI, BoosterTracks.GCN_DK_MOUNTAIN,
             BoosterTracks.WII_DAISY_CIRCUIT, BoosterTracks.TOUR_PIRANHA_PLANT_COVE)
    SPINY = (BoosterTracks.TOUR_MADRID_DRIVE, BoosterTracks.MK7_ROSALINA_ICE_WORLD,
             BoosterTracks.SNES_BOWSER_CASTLE_3, BoosterTracks.WII_RAINBOW_ROAD)


class Characters(IntEnum):
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
    BIRDO = 0x2C
    KAMEK = 0x2D
    PETEY_PIRANHA = 0x2E
    WIGGLER = 0x2F
    DIDDY_KONG = 0x30
    FUNKY_KONG = 0x31
    PEACHETTE = 0x32
    PAULINE = 0x33
    MII2 = 0x34


class MK8VehicleBodies(IntEnum):
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
class MK8DXVehicleBodies(IntEnum):
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


class Tires(IntEnum):
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


class Gliders(IntEnum):
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


class Weekdays(IntEnum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6


class WeightClass(IntEnum):
    LIGHT = 0
    MEDIUM = 1
    HEAVY = 2


class Teams(IntEnum):
    RED = 0
    BLUE = 1
    SOLO = 2
