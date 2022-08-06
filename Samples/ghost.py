import logging
import os

import anyio
from anynet import http
from dotenv import load_dotenv
from nintendo.nex import backend, datastore
from nintendo.nex.ranking import RankingClient, RankingMode, RankingOrderCalc, RankingOrderParam

from mk8boards.common import MK8Tracks as Tracks
from mk8boards.mk8.boards_client import MK8Client
from mk8boards.mk8.extract_info import MK8GhostInfo, MK8PlayerInfo

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Device Information
DEVICE_ID = int(os.getenv("DEVICE_ID"), base=16)
SERIAL_NUMBER = os.getenv("SERIAL_NUMBER")
SYSTEM_VERSION = int(os.getenv("SYSTEM_VERSION"), base=16)
# Account Information
USERNAME = os.getenv("NNID_USERNAME")
PASSWORD = os.getenv("PASSWORD")
# Region and Language Information
COUNTRY_ID = int(os.getenv("REGION_ID"))
COUNTRY_NAME = os.getenv("COUNTRY_NAME")
REGION_ID = int(os.getenv("REGION_ID"))
REGION_NAME = os.getenv("REGION_NAME")
LANGUAGE = os.getenv("LANGUAGE")

# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
TRACK_ID = Tracks.GCN_YOSHI_CIRCUIT.id_
NNID = "Dinostraw"  # NNID of targeted player


async def get_common_data(client: MK8Client, nnid: str) -> bytes:
    order_param = RankingOrderParam()
    order_param.order_calc = RankingOrderCalc.STANDARD
    order_param.offset = 0
    order_param.count = 1

    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            ranking_client = RankingClient(be_client)
            rankings = await ranking_client.get_ranking(RankingMode.SELF, TRACK_ID, order_param,
                                                        0, await client.nnas.get_pid(nnid))
            return rankings.data[0].common_data


async def get_ghost(client: MK8Client, nnid: str) -> bytes:
    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            store = datastore.DataStoreClient(be_client)

            get_param = datastore.DataStorePrepareGetParam()
            get_param.persistence_target.owner_id = await client.nnas.get_pid(nnid)
            get_param.persistence_target.persistence_id = TRACK_ID - 16
            get_param.extra_data = ["WUP", str(REGION_ID), REGION_NAME, str(COUNTRY_ID), COUNTRY_NAME, ""]

            req_info = await store.prepare_get_object(get_param)
            headers = {header.key: header.value for header in req_info.headers}
            response = await http.get(req_info.url, headers=headers)
            response.raise_if_error()

            return response.body


async def main():
    mk8_client = MK8Client(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION, COUNTRY_ID,
                           COUNTRY_NAME, REGION_ID, REGION_NAME, LANGUAGE,
                           USERNAME, PASSWORD)
    await mk8_client.login()

    ghost_data = await get_ghost(mk8_client, NNID)
    ghost_info = MK8GhostInfo(ghost_data)
    print(ghost_info, end="\n\n")
    print("Internal Mii Name:", ghost_info.mii.mii_name)
    print("Internal Mii Creator:", ghost_info.mii.creator_name)
    print("Internal Mii Creator ID:", ''.join(f"{x:02X}" for x in ghost_info.mii.author_id))
    print("Internal Mii MAC Address:", ''.join(f"{x:02X}" for x in ghost_info.mii.mac_address))
    print(f"https://studio.mii.nintendo.com/miis/image.png?data="
          f"{''.join(f'{x:02x}' for x in ghost_info.mii.to_studio_api())}"
          f"&width=512&type=face", end="\n\n")
    filename = ghost_info.generate_filename()
    print(f"Filename:\n{filename}")
    with open("../Output/Ghosts/" + filename, "wb") as f:
        f.write(ghost_data)

    common_data = await get_common_data(mk8_client, NNID)
    player_info = MK8PlayerInfo(common_data)
    print("Current Mii Name:", player_info.mii.mii_name)
    print("Internal Mii Creator:", player_info.mii.creator_name)
    print("Internal Mii Creator ID:", ''.join(f"{x:02X}" for x in player_info.mii.author_id))
    print("Internal Mii MAC Address:", ''.join(f"{x:02X}" for x in player_info.mii.mac_address))
    print(f"https://studio.mii.nintendo.com/miis/image.png?data="
          f"{''.join(f'{x:02x}' for x in player_info.mii.to_studio_api())}"
          f"&width=512&type=face")
    # with open("../Output/Common Data/common_data.bin", "wb") as f:
    #     f.write(common_data)


anyio.run(main)
