import logging

import anyio
from nintendo.nex import backend, ranking, settings

from mk8boards.common import MK8DXGameInfo, MK8Tracks

logging.basicConfig(level=logging.INFO)

# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
TRACK_ID = MK8Tracks.MARIO_CIRCUIT - 16
HOST = "g%08x-lp1.s.n.srv.nintendo.net" % MK8DXGameInfo.GAME_SERVER_ID
PORT = 443


def format_time(score):
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60
    return f'{minutes}:{seconds:02d}.{millisec:03d}'


async def main():
    s = settings.load("switch")
    s.configure(MK8DXGameInfo.ACCESS_KEY, MK8DXGameInfo.NEX_VERSION)
    async with backend.connect(s, HOST, PORT) as be:
        async with be.login_guest() as client:
            ranking_client = ranking.RankingClient(client)

            order_param = ranking.RankingOrderParam()
            order_param.order_calc = ranking.RankingOrderCalc.ORDINAL
            order_param.offset = 0  # Start at 500th place
            order_param.count = 20  # Download 20 records

            rankings = await ranking_client.get_ranking(
                ranking.RankingMode.GLOBAL, TRACK_ID,
                order_param, 0, 0
            )

            ranking_stats = await ranking_client.get_stats(
                TRACK_ID, order_param, ranking.RankingStatFlags.ALL
            )

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
                print(f'\t{rankdata.rank:5d}   {time}')


anyio.run(main)
