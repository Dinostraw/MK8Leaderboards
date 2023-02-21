import asyncio
from dataclasses import dataclass
from typing import Dict, List, Union

from nintendo.nex.ranking import RankingClient, RankingOrderCalc, RankingOrderParam, RankingStatFlags

from mk8boards.common import MK8Tracks
from mk8boards.mk8.timesheet import format_time


@dataclass
class TrackStats:
    num_records: int
    sum_of_times: int
    best_time: int
    worst_time: int
    average_time: float


def format_all_stats(stats: Dict[str, TrackStats]) -> str:
    stat_str = ("Track  |  Total Times    Average Time    Sum of Uploaded Times    Slowest Time\n"
                f" abbr  |{'':>13s}{'m:ss.xxx':>16s}{'year:day:hr:mm:ss.xxx':>25s}{'m:ss.xxx':>16s}\n"
                + '=' * 78 + '\n')

    def gen_stat_string():
        for x, (track, tstats) in enumerate(stats.items()):
            sum_time = format_total_time(tstats.sum_of_times)
            wt = format_time(tstats.worst_time)
            avg = format_time(tstats.average_time)
            yield (f"{track:>5s}  |  {tstats.num_records:>11d}    {avg:>12s}    "
                   f"{sum_time:>21s}    {wt:>12s}")

    return stat_str + '\n'.join(gen_stat_string())


def format_total_time(score: Union[int, float]) -> str:
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60 % 60
    hours = score // 1000 // 60 // 60 % 24
    days = score // 1000 // 60 // 60 // 24 % 365
    years = score // 1000 // 60 // 60 // 24 // 365
    return "%i:%03i:%02i:%02i:%02i.%03i" % (years, days, hours, minutes, seconds, millisec)


async def get_stats(ranking_client: RankingClient, tracks: Union[MK8Tracks, List[MK8Tracks]])\
        -> Dict[str, TrackStats]:
    if not isinstance(tracks, list):
        tracks = [tracks]

    order_param = RankingOrderParam()
    order_param.order_calc = RankingOrderCalc.STANDARD
    order_param.offset = 0  # Start at 1st place
    order_param.count = 0  # Download literally nothing

    tasks = [asyncio.ensure_future(ranking_client.get_stats(
        track.id_, order_param, RankingStatFlags.ALL)
    ) for track in tracks]

    track_stats = await asyncio.gather(*tasks)
    return {track.abbr: TrackStats(num_records=int(ts.stats[0]), sum_of_times=int(ts.stats[1]),
                                   best_time=int(ts.stats[2]), worst_time=int(ts.stats[3]),
                                   average_time=ts.stats[4])
            for track, ts in zip(tracks, track_stats)}
