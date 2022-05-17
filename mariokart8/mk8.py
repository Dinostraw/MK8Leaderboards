import json
import os
from enum import Enum
from typing import Any, Callable

from nintendo import nnas
from nintendo.games import MK8
from nintendo.nex import settings, backend
from nintendo.nex.ranking import RankingClient

from str_mappings import standardize_abbr


class MK8Client:
    async def login(self) -> None:
        self.access_token = await self.nnas.login(self.username, self.password)
        self.nex_token = await self.nnas.get_nex_token(self.access_token.token, MK8.GAME_SERVER_ID)

    # Perhaps use this as a wrapper function instead of repeating code?
    # async def connect_and_run(self, func: Callable, *args, **kwargs) -> Any:
    #     async with backend.connect(self.settings, self.nex_token.host, self.nex_token.port) as be:
    #         async with be.login(str(self.nex_token.pid), self.nex_token.password) as client:
    #             ranking_client = RankingClient(client)
    #             return await func(ranking_client, *args, **kwargs)

    def __init__(self, device_id: int, serial_num: str, system_ver: int, country_id: int,
                 country_name: str, region_id: int, region_name: str, lang: str,
                 username: str, password: str):
        self.device_id = device_id
        self.serial_num = serial_num
        self.system_ver = system_ver
        self.country_id = country_id
        self.country_name = country_name
        self.region_id = region_id
        self.region_name = region_name
        self.lang = lang
        self.username = username
        self.password = password

        self.nnas = nnas.NNASClient()
        self.nnas.set_device(self.device_id, self.serial_num, self.system_ver)
        self.nnas.set_title(MK8.TITLE_ID_EUR, MK8.LATEST_VERSION)
        self.nnas.set_locale(self.region_id, self.country_name, self.lang)
        self.settings = settings.default()
        self.settings.configure(MK8.ACCESS_KEY, MK8.NEX_VERSION)
        self.access_token = None
        self.nex_token = None


# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
class MK8Tracks(Enum):
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

    GCN_YOSHI_CIRCUIT = ("GCN Yoshi Circuit", "dYC", 56)
    EXCITEBIKE_ARENA = ("Excitebike Arena", "dEA", 53)
    DRAGON_DRIFTWAY = ("Dragon Driftway", "dDD", 50)
    MUTE_CITY = ("Mute City", "dMC", 49)

    WII_WARIO_GOLD_MINE = ("Wii Wario's Gold Mine", "dWGM", 57)
    SNES_RAINBOW_ROAD = ("SNES Rainbow Road", "dRR", 58)
    ICE_ICE_OUTPOST = ("Ice Ice Outpost", "dIIO", 55)
    HYRULE_CIRCUIT = ("Hyrule Circuit", "dHC", 51)

    GCN_BABY_PARK = ("GCN Baby Park", "dBP", 61)
    GBA_CHEESE_LAND = ("GBA Cheese Land", "dCL", 62)
    WILD_WOODS = ("Wild Woods", "dWW", 54)
    ANIMAL_CROSSING = ("Animal Crossing", "dAC", 52)

    MK7_NEO_BOWSER_CITY = ("3DS Neo Bowser City", "dNBC", 60)
    GBA_RIBBON_ROAD = ("GBA Ribbon Road", "dRiR", 59)
    SUPER_BELL_SUBWAY = ("Super Bell Subway", "dSBS", 48)
    BIG_BLUE = ("Big Blue", "dBB", 63)

    def __init__(self, fullname: str, abbr: str, id_: int):
        self.fullname = fullname
        self.abbr = abbr
        self.id_ = id_


# Each cup has 4 predefined courses
class MK8Cups(Enum):
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

    def __init__(self, track0: MK8Tracks, track1: MK8Tracks, track2: MK8Tracks, track3: MK8Tracks):
        self.track0 = track0
        self.track1 = track1
        self.track2 = track2
        self.track3 = track3


with open(os.path.join(os.path.dirname(__file__), "mk8_track_abbr.json"), encoding="utf-8") as f:
    abbr_aliases = {standardize_abbr(abbr): MK8Tracks[track]
                    for track, abbrs in json.load(f).items()
                    for abbr in abbrs}
