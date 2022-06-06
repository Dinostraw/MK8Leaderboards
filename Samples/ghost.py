import logging
import os

import anyio
from anynet import http
from dotenv import load_dotenv
from nintendo.nex import backend, datastore
from nintendo.nex.ranking import RankingClient, RankingMode, RankingOrderCalc, RankingOrderParam

from mariokart8.extract_info import MK8GhostInfo
from mariokart8.mk8 import MK8Client, MK8Tracks as Tracks

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
TRACK_ID = Tracks.N64_RAINBOW_ROAD.id_
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
    info = MK8GhostInfo(ghost_data)
    print(info)
    filename = info.generate_filename()
    print(filename)
    with open("./Output/Ghosts/" + filename, "wb") as f:
        f.write(ghost_data)

    # common_data = await get_common_data(mk8_client, NNID)
    # with open("./Output/Common Data/common_data.bin", "wb") as f:
    #     f.write(common_data)


anyio.run(main)
