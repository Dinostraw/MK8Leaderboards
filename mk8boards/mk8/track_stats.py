import asyncio
from typing import Dict, List, Union

from nintendo.nex.ranking import RankingClient, RankingOrderCalc, RankingOrderParam, RankingStatFlags

from mk8boards.common import MK8Tracks
from mk8boards.mk8.timesheet import format_time


def format_all_stats(stats: Dict[str, List[float]]) -> str:
    stat_str = ("Track  |  Total Times    Average Time    Sum of Uploaded Times    Slowest Time\n"
                + f" abbr  |{'':>13s}{'m:ss.xxx':>16s}{'year:day:hr:mm:ss.xxx':>25s}{'m:ss.xxx':>16s}\n"
                + '=' * 78 + '\n')

    for x, track in enumerate(stats):
        total = stats[track][0]  # Total number of uploaded times
        sum_time = format_total_time(stats[track][1])  # Sum of uploaded times
        wt = format_time(stats[track][3])  # Worst time
        avg = format_time(stats[track][4])  # Average of uploaded times
        stat_str += f"{track:>5s}  |  {int(total):>11d}    {avg:>12s}    {sum_time:>21s}    {wt:>12s}\n"
        if x % 4 == 3:
            stat_str += ""
    return stat_str


def stats_to_labeled_dict(stats: List[float]) -> Dict[str, Union[str, int]]:
    total = stats[0]  # Total number of uploaded times
    sum_time = format_total_time(stats[1])  # Sum of uploaded times
    wt = format_time(stats[3])  # Worst time
    avg = format_time(stats[4])  # Average of uploaded times

    return {"Total Times": int(total), "Average Time": avg,
            "Sum of Uploaded Times": sum_time, "Slowest Time": wt}


def format_total_time(score: Union[int, float]) -> str:
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60 % 60
    hours = score // 1000 // 60 // 60 % 24
    days = score // 1000 // 60 // 60 // 24 % 365
    years = score // 1000 // 60 // 60 // 24 // 365
    return "%i:%03i:%02i:%02i:%02i.%03i" % (years, days, hours, minutes, seconds, millisec)


async def get_stats(ranking_client: RankingClient, tracks: Union[MK8Tracks, List[MK8Tracks]])\
        -> Dict[str, List[float]]:
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
    return {track.abbr: ts.stats for track, ts in zip(tracks, track_stats)}
