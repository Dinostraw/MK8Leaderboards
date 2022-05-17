import logging
import os

import anyio
from anynet import http
from nintendo import nnas
from nintendo.games import MK8
from nintendo.nex import backend, ranking, settings, datastore

from mariokart8.extract_info import MK8GhostInfo
from mariokart8.mk8 import MK8Tracks as Tracks

logging.basicConfig(level=logging.INFO)

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
REGION_ID = os.getenv("REGION_ID")
REGION_NAME = os.getenv("REGION_NAME")
LANGUAGE = os.getenv("LANGUAGE")
# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
TRACK_ID = Tracks.MARIO_KART_STADIUM.id_


def format_time(score):
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60
    return "%i:%02i.%03i" % (minutes, seconds, millisec)


async def main():
    nas = nnas.NNASClient()
    nas.set_device(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION)
    nas.set_title(MK8.TITLE_ID_EUR, MK8.LATEST_VERSION)
    nas.set_locale(REGION_ID, COUNTRY_NAME, LANGUAGE)

    access_token = await nas.login(USERNAME, PASSWORD)
    nex_token = await nas.get_nex_token(access_token.token, MK8.GAME_SERVER_ID)

    s = settings.default()
    s.configure(MK8.ACCESS_KEY, MK8.NEX_VERSION)
    async with backend.connect(s, nex_token.host, nex_token.port) as be:
        async with be.login(str(nex_token.pid), nex_token.password) as client:
            ranking_client = ranking.RankingClient(client)

            order_param = ranking.RankingOrderParam()
            order_param.order_calc = ranking.RankingOrderCalc.ORDINAL
            order_param.offset = 212  # Start at 500th place
            order_param.count = 100  # Download 20 records

            rankings = await ranking_client.get_ranking(
                ranking.RankingMode.GLOBAL, TRACK_ID,
                order_param, 0, 0
            )

            ranking_stats = await ranking_client.get_stats(
                TRACK_ID, order_param, ranking.RankingStatFlags.ALL
            )

            names = await nas.get_nnids([data.pid for data in rankings.data])

            # Print some interesting stats
            stats = ranking_stats.stats
            print("Total:", int(stats[0]))
            print("Total time:", format_time(stats[1]))
            print("Lowest time:", format_time(stats[2]))
            print("Highest time:", format_time(stats[3]))
            print("Average time:", format_time(stats[4]))

            print("Rankings:")
            for rankdata in rankings.data:
                time = format_time(rankdata.score)
                print("\t%5i   %20s   %s" % (rankdata.rank, names[rankdata.pid], time))

            # Let's download the replay file of whoever is in 500th place
            store = datastore.DataStoreClient(client)

            rankdata = rankings.data[0]
            get_param = datastore.DataStorePrepareGetParam()
            get_param.persistence_target.owner_id = rankdata.pid
            get_param.persistence_target.persistence_id = TRACK_ID - 16
            get_param.extra_data = ["WUP", str(REGION_ID), REGION_NAME, str(COUNTRY_ID), COUNTRY_NAME, ""]

            req_info = await store.prepare_get_object(get_param)
            headers = {header.key: header.value for header in req_info.headers}
            response = await http.get(req_info.url, headers=headers)
            response.raise_if_error()

            info = MK8GhostInfo(response.body)
            print(info)
            filename = info.generate_filename()
            print(filename)
            with open("./Output/Ghosts/" + filename, "wb") as f:
                f.write(response.body)
            with open("./Output/Common Data/common_data7.bin", "wb") as f:
                f.write(rankdata.common_data)

anyio.run(main)
