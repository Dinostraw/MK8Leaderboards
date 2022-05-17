import asyncio
from collections import ChainMap
from typing import Union

from nintendo.nex import backend
from nintendo.nex.ranking import RankingClient, RankingMode, RankingOrderParam, RankingResult
from nintendo.nnas import NNASClient

from mariokart8.mk8 import MK8Client


async def get_boards_stub(ranking_client: RankingClient, order_param: RankingOrderParam,
                          track_id: int, pid: Union[int, None]) -> RankingResult:
    if order_param.count > 255:
        order_param.count = 255
    if pid:
        boards = await ranking_client.get_ranking(
            RankingMode.GLOBAL_AROUND_SELF, track_id,
            order_param, 0, pid
        )
    else:
        boards = await ranking_client.get_ranking(
            RankingMode.GLOBAL, track_id,
            order_param, 0, 0
        )
    return boards


async def get_boards(client: MK8Client, order_param: RankingOrderParam, track_id: int,
                     pid: Union[int, None] = None) -> RankingResult:
    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            ranking_client = RankingClient(be_client)
            # Necessary in the case that order_param.count exceeds 255
            remaining = order_param.count

            # Ignore offset if PID is present
            if pid:
                order_param.offset = 1

            boards = await get_boards_stub(ranking_client, order_param, track_id, pid)

            # Return early if requested amount is 255 or less
            if remaining <= 255:
                return boards

            # Subtract 254 instead of 255 in order to prevent double-counting a record
            # and thus prevent returning one fewer record than the amount requested
            remaining -= 254

            # Set to 1 to be able to get times that are slower than that of a particular player
            order_param.offset = 1

            # Loop until requested amount is exhausted
            while remaining > 0:
                order_param.count = remaining if remaining <= 255 else 255
                pid = boards.data[-1].pid  # Get last PID in list to use as the base for the next request

                frag = await get_boards_stub(ranking_client, order_param, track_id, pid)
                boards.data.extend(frag.data[1:])
                remaining -= 254

                if order_param.count != len(frag.data):
                    break

    return boards


async def get_nnids_from_boards(nnas_client: NNASClient, boards) -> ChainMap:
    max_amount = 500
    sem = asyncio.Semaphore(32)  # Prevent flooding servers

    # https://stackoverflow.com/a/60004447
    async def sem_get_nnids(x):
        async with sem:
            return await nnas_client.get_nnids(x)

    tasks = [
        asyncio.ensure_future(sem_get_nnids([data.pid for data in boards.data[x:x + max_amount]]))
        for x in range(0, len(boards.data), max_amount)
    ]
    nnids = await asyncio.gather(*tasks)
    return ChainMap(*nnids)
