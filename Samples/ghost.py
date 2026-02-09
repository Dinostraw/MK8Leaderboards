import logging
import os

import anyio
from anynet import http
from dotenv import load_dotenv
from nintendo.nex import datastore
from nintendo.nex.ranking import (RankingClient, RankingMode, RankingOrderCalc,
                                  RankingOrderParam, RankingRankData)

from mk8boards.common import MK8Tracks as Tracks
from mk8boards.mk8.boards_client import MK8Client
from mk8boards.mk8.structures import MK8GhostInfo, MK8PlayerInfo

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# --- Device Information ---
DEVICE_ID = int(os.getenv("DEVICE_ID"), base=16)
DEVICE_CERT = os.getenv("DEVICE_CERT")  # Optional on Nintendo Network
SERIAL_NUMBER = os.getenv("SERIAL_NUMBER")
SYSTEM_VERSION = int(os.getenv("SYSTEM_VERSION"), base=16)
# --- Region and Language Information ---
COUNTRY_ID = int(os.getenv("COUNTRY_ID"))
COUNTRY_NAME = os.getenv("COUNTRY_NAME")
REGION_ID = int(os.getenv("REGION_ID"))
REGION_NAME = os.getenv("REGION_NAME")
LANGUAGE = os.getenv("LANGUAGE")
# --- Account Information ---
USERNAME = os.getenv("NNID_USERNAME")
PASSWORD_HASH = os.getenv("PASSWORD_HASH")
# --- Server Information ---
USE_PRETENDO = os.getenv("USE_PRETENDO").lower() == 'true'

# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
TRACK_ID = Tracks.THWOMP_RUINS.value
NNID = "TheRealAli-A"  # NNID of targeted player


class GhostResult:
    def __init__(self, rankdata: RankingRankData, ghost_response: http.HTTPResponse):
        self.pid = rankdata.pid
        self.unique_id = rankdata.unique_id
        self.rank = rankdata.rank
        self.category = rankdata.category
        self.score = rankdata.score
        self.motion = bool(rankdata.groups[0])
        self.param = rankdata.param
        self.common_data = rankdata.common_data
        self.ghost_data = ghost_response.body
        self.upload_time = ghost_response.headers["Last-Modified"]


async def get_ghost(client: MK8Client, nnid: str) -> GhostResult:
    order_param = RankingOrderParam()
    order_param.order_calc = RankingOrderCalc.STANDARD
    order_param.offset = 0
    order_param.count = 1

    pid = await client.nnas.get_pid(nnid)

    async with client.backend_login() as bc:
        rankings = await RankingClient(bc).get_ranking(RankingMode.SELF, TRACK_ID, order_param, 0, pid)
        rankdata = rankings.data[0]

        store = datastore.DataStoreClient(bc)

        get_param = datastore.DataStorePrepareGetParam()
        get_param.persistence_target.owner_id = pid
        get_param.persistence_target.persistence_id = TRACK_ID - 16
        get_param.extra_data = ["WUP", str(REGION_ID), REGION_NAME, str(COUNTRY_ID), COUNTRY_NAME, ""]

        req_info = await store.prepare_get_object(get_param)
        headers = {header.key: header.value for header in req_info.headers}
        response = await http.get(req_info.url, headers=headers)
        response.raise_if_error()

        return GhostResult(rankdata, response)


async def main():
    client = MK8Client()
    client.set_device(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION, DEVICE_CERT)
    client.set_locale(REGION_ID, REGION_NAME, COUNTRY_ID, COUNTRY_NAME, LANGUAGE)
    if USE_PRETENDO:
        client.nnas.set_url('account.pretendo.cc')
        # Reset TLS context to defaults
        client.nnas.context.set_certificate_chain(None, None)
        client.nnas.context.set_authority(None)
    await client.login(USERNAME, PASSWORD_HASH, password_type='hash')

    ghost_result = await get_ghost(client, NNID)
    true_nnid = await client.nnas.get_nnid(ghost_result.pid)
    ghost_info = MK8GhostInfo(ghost_result.ghost_data, motion=ghost_result.motion)
    player_info = MK8PlayerInfo(ghost_result.common_data)

    print("Ghost Data Information")
    print("======================")
    print(ghost_info, end="\n\n")
    print("Upload Timestamp:", ghost_result.upload_time, end="\n\n")
    print("Internal Mii Name:", ghost_info.mii.mii_name)
    print(f"Internal Mii Birthday: {ghost_info.mii.birth_day}-{ghost_info.mii.birth_month}")
    print("Internal Mii Creator:", ghost_info.mii.creator_name)
    print("Internal Mii Creator ID:", ''.join(f"{x:02X}" for x in ghost_info.mii.author_id))
    print("Internal Mii MAC Address:", ''.join(f"{x:02X}" for x in ghost_info.mii.mac_address))
    print(f"https://studio.mii.nintendo.com/miis/image.png?data="
          f"{''.join(f'{x:02x}' for x in ghost_info.mii.to_studio_api())}"
          f"&width=512&type=face", end="\n\n")
    filename = ghost_info.generate_filename()
    print(f"Filename:\n{filename}\n\n")

    print("Common Data Information")
    print("=======================")
    print("Current Mii Name:", player_info.mii.mii_name)
    print(f"Current Mii Birthday: {player_info.mii.birth_day}-{player_info.mii.birth_month}")
    print("Current Mii Creator:", player_info.mii.creator_name)
    print("Current Mii Creator ID:", ''.join(f"{x:02X}" for x in player_info.mii.author_id))
    print("Current Mii MAC Address:", ''.join(f"{x:02X}" for x in player_info.mii.mac_address))
    print(f"https://studio.mii.nintendo.com/miis/image.png?data="
          f"{''.join(f'{x:02x}' for x in player_info.mii.to_studio_api())}"
          f"&width=512&type=face")

    if USE_PRETENDO:
        output_dir = f"../Output/Ghosts/Pretendo/DL/{true_nnid}"
    else:
        output_dir = f"../Output/Ghosts/DL/{true_nnid}"
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/{filename}", "wb") as f:
        f.write(ghost_info.header)
        f.write(ghost_info.data)

    # with open("../Output/Common Data/common_data.bin", "wb") as f:
    #     f.write(ghost_result.common_data)

    # with open("../Output/mii.3dsmii", "wb") as f:
    #     f.write(ghost_result.common_data[0x14:0x70])


anyio.run(main)
