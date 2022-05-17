import logging

import anyio
from nintendo.nex import backend, ranking, settings

logging.basicConfig(level=logging.INFO)

# Track IDs: https://github.com/Kinnay/NintendoClients/wiki/Mario-Kart-8-Track-IDs
TRACK_ID = 10
HOST = "g%08x-lp1.s.n.srv.nintendo.net" % 0x2B309E01
PORT = 443


def format_time(score):
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60
    return "%i:%02i.%03i" % (minutes, seconds, millisec)


async def main():
    s = settings.load("switch")
    s.configure("09c1c475", 40302)
    async with backend.connect(s, HOST, PORT) as be:
        async with be.login("GUEST", password="MMQea3n!fsik") as client:
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
                print("\t%5i   %s" % (rankdata.rank, time))


anyio.run(main)
