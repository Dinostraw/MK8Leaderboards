import asyncio
import json
import os
from collections import ChainMap, namedtuple
from typing import Union

from nintendo.nex import backend
from nintendo.nex.ranking import RankingClient, RankingMode, RankingOrderCalc
from nintendo.nex.ranking import RankingOrderParam, RankingResult
from nintendo.nnas import NNASClient

from mk8boards.mk8.mk8 import MK8Client

_AltInfo = namedtuple("_AltInfo", ["main", "alts"])
with open(os.path.join(os.path.dirname(__file__), "filters/alts.json"), 'r') as f:
    _alts = {int(main): _AltInfo(True, [int(alt) for alt in alts])
             for main, alts in json.load(f).items()}
_alts.update({alt: _AltInfo(False, [main]) for main, info in _alts.items() for alt in info.alts})

with open(os.path.join(os.path.dirname(__file__), "filters/banned.txt"), 'r') as f:
    _banned = {int(line.strip()) for line in f.readlines()}

with open(os.path.join(os.path.dirname(__file__), "filters/blacklist.json"), 'r') as f:
    _blacklist = {int(main): {int(alt) for alt in alts} for main, alts in json.load(f).items()}

with open(os.path.join(os.path.dirname(__file__), "filters/hacked.txt"), 'r') as f:
    _hacked = {int(line.strip()) for line in f.readlines()}


def filter_boards(boards: RankingResult, hacked: bool = True, banned: bool = True,
                  alts: bool = True, reindex: bool = True) -> RankingResult:
    data = boards.data
    tid = boards.data[0].category
    if hacked:
        data = list(filter(lambda x: x.pid not in _hacked, data))
        data = list(filter(lambda x: tid not in _blacklist[x.pid] if x.pid in _blacklist else True, data))

    if banned:
        data = list(filter(lambda x: x.pid not in _banned, data))

    if alts:
        alts_set = set()
        for x in data:
            if x.pid not in _alts or x.pid in alts_set:
                continue
            if _alts[x.pid].main is True:
                alts_set.update(_alts[x.pid].alts)
            else:
                main_pid = _alts[x.pid].alts[0]
                alts_set.add(main_pid)
                alts_set.update([pid for pid in _alts[main_pid].alts if x.pid != pid])
        data = list(filter(lambda x: x.pid not in alts_set, data))

    if reindex and (hacked or banned or alts) and len(data) > 0:
        data[0].rank = 1
        if len(data) > 1:
            prev = data[0]
            for i, x in enumerate(data[1:], start=2):
                if x.score != prev.score:
                    x.rank = i
                else:
                    x.rank = prev.rank
                prev = x

    result = RankingResult()
    result.data = data
    result.since_time = boards.since_time
    result.total = boards.total
    return result


async def get_boards_stub(ranking_client: RankingClient, track_id: int, order_param: RankingOrderParam,
                          pid: Union[int, None]) -> RankingResult:
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


async def get_boards(client: MK8Client, track_id: int, offset: int, count: int,
                     pid: Union[int, None] = None) -> RankingResult:
    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            ranking_client = RankingClient(be_client)

            order_param = RankingOrderParam()
            order_param.order_calc = RankingOrderCalc.STANDARD
            order_param.offset = offset
            order_param.count = count

            # Necessary in the case that order_param.count exceeds 255
            remaining = order_param.count

            # Ignore offset if PID is present
            if pid:
                order_param.offset = 1

            boards = await get_boards_stub(ranking_client, track_id, order_param, pid)

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

                frag = await get_boards_stub(ranking_client, track_id, order_param, pid)
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
