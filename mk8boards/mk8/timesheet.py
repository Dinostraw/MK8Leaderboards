import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Dict, List, Union

from nintendo.nex import backend, common
from nintendo.nex.ranking import RankingClient, RankingMode, RankingOrderCalc
from nintendo.nex.ranking import RankingOrderParam, RankingRankData
from nintendo.nnas import NNASError

from mk8boards.mk8.extract_info import MK8PlayerInfo
from mk8boards.mk8.mk8 import MK8Tracks, MK8Client


@dataclass(frozen=True)
class Timesheet:
    pid: int
    nnid: str = ""
    mii_name: str = ""
    records: Dict[str, RankingRankData] = field(default_factory=dict)

    # Convenient wrapper for module-level function
    @staticmethod
    def format_time(score: Union[int, float]) -> str:
        return format_time(score)

    def to_string_array(self) -> List[str]:
        time_strings = []
        for track, rankdata in self.records.items():
            try:
                ts = self.format_time(rankdata.score)
                time_strings.append("%-4s    %7i    %s" % (track, rankdata.rank, ts))
            except AttributeError:
                time_strings.append("%-4s    -------    -:--.---" % track)
        return time_strings


@dataclass(frozen=True)
class Matchup:
    p1_timesheet: Timesheet
    p2_timesheet: Timesheet
    p1_wins: int = 0
    p2_wins: int = 0
    ties: int = 0


def format_time(score: Union[int, float]) -> str:
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60
    return "%i:%02i.%03i" % (minutes, seconds, millisec)


def get_matchup(timesheet1: Timesheet, timesheet2: Timesheet) -> Matchup:
    p1_times = timesheet1.records
    p2_times = timesheet2.records
    p1_wins = p2_wins = ties = 0
    tracks = p1_times.keys() & p2_times.keys()
    for track in tracks:
        if p1_times[track] is None or p2_times[track] is None:
            continue
        elif p1_times[track].score < p2_times[track].score:
            p1_wins += 1
        elif p1_times[track].score > p2_times[track].score:
            p2_wins += 1
        else:
            ties += 1
    return Matchup(timesheet1, timesheet2, p1_wins=p1_wins, p2_wins=p2_wins, ties=ties)


async def get_time(pid: int, track_id: int, ranking_client: RankingClient,
                   order_param: RankingOrderParam) -> RankingRankData:
    try:
        time = (await ranking_client.get_ranking(
            RankingMode.SELF, track_id, order_param, 0, pid
        )).data[0]
    except common.RMCError:
        time = None
    return time


async def get_times(pids: List[int], track_id: int, ranking_client: RankingClient,
                    order_param: RankingOrderParam) -> Dict[str, RankingRankData]:
    # Initializes each time to None in case no times are found
    times = {pid: None for pid in pids}
    with suppress(common.RMCError):
        records = (await ranking_client.get_ranking_by_pid_list(
            pids, RankingMode.GLOBAL, track_id, order_param, 0
        )).data
        for rankdata in records:
            if rankdata.pid not in pids:
                continue
            times[rankdata.pid] = rankdata
    return times


async def get_timesheet(client: MK8Client, nnid: str) -> Timesheet:
    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            ranking_client = RankingClient(be_client)

            order_param = RankingOrderParam()
            order_param.order_calc = RankingOrderCalc.STANDARD
            order_param.offset = 0
            order_param.count = 1

            pid = await client.nnas.get_pid(nnid)

            tasks = [
                asyncio.ensure_future(get_time(pid, track.id_, ranking_client, order_param))
                for track in MK8Tracks
            ]
            times = await asyncio.gather(*tasks)
            timesheet = {track.abbr: time for track, time in zip(MK8Tracks, times)}

            try:
                mii_name = (await client.nnas.get_mii(pid)).name
            except NNASError:
                mii_name = ""
                for time in timesheet.values():
                    if time is not None:
                        mii_name = MK8PlayerInfo(time.common_data).mii_name
                        break

            return Timesheet(pid, nnid, mii_name, timesheet)


async def get_timesheets(client: MK8Client, nnids: List[str]) -> List[Timesheet]:
    async with backend.connect(client.settings, client.nex_token.host, client.nex_token.port) as be:
        async with be.login(str(client.nex_token.pid), client.nex_token.password) as be_client:
            ranking_client = RankingClient(be_client)

            order_param = RankingOrderParam()
            order_param.order_calc = RankingOrderCalc.STANDARD
            order_param.offset = 0
            order_param.count = len(nnids) + 1

            pids = await client.nnas.get_pids(nnids)
            # Try-block is necessary in case all the requested accounts have since been deleted
            try:
                miis = {mii.pid: mii for mii in (await client.nnas.get_miis(pids.values()))}
            except NNASError:
                miis = {}

            tasks = [
                asyncio.ensure_future(get_times(pids.values(), track.id_, ranking_client, order_param))
                for track in MK8Tracks
            ]
            times = await asyncio.gather(*tasks)

            timesheets = []
            for nnid, pid in pids.items():
                records = {track.abbr: time[pid] for track, time in zip(MK8Tracks, times)}
                if pid in miis:
                    nnid = miis[pid].nnid
                    mii_name = miis[pid].name
                else:
                    mii_name = ""
                    for time in records.values():
                        if time is not None:
                            mii_name = MK8PlayerInfo(time.common_data).mii_name
                            break
                timesheets.append(Timesheet(pid, nnid, mii_name, records))

            return timesheets


# async def timesheet_test(ranking_client: RankingClient, nnas_client: NNASClient, nnid: str) -> Timesheet:
#     order_param = RankingOrderParam()
#     order_param.order_calc = RankingOrderCalc.STANDARD
#     order_param.offset = 0
#     order_param.count = 1
#
#     pid = await nnas_client.get_pid(nnid)
#     mii_name = (await nnas_client.get_mii(pid)).name
#
#     tasks = [
#         asyncio.ensure_future(get_time(pid, track.id_, ranking_client, order_param))
#         for track in MK8Tracks
#     ]
#     times = await asyncio.gather(*tasks)
#     timesheet = {track.abbr: time for track, time in zip(MK8Tracks, times)}
#     return Timesheet(pid, nnid, mii_name, timesheet)
