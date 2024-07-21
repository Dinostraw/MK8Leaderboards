import asyncio
import calendar
import io
import logging
import os

import discord
from anynet import http
from discord.ext import commands
from dotenv import load_dotenv
from nintendo.nex import datastore
from nintendo.nex.common import RMCError
from nintendo.nex.ranking import RankingClient, RankingRankData, RankingOrderParam, RankingOrderCalc, RankingMode
from nintendo.nnas import NNASError

from mk8boards.common import MK8Cups, MK8Tracks
from mk8boards.mk8 import timesheet as ts
from mk8boards.mk8.boards_client import MK8Client
from mk8boards.mk8.structures import MK8PlayerInfo, MK8GhostInfo
from mk8boards.mk8.timesheet import format_time
from mk8boards.mk8.track_stats import get_stats, format_total_time

logging.basicConfig(level=logging.WARNING)

# Load environment variables
load_dotenv()

# --- Device Information ---
DEVICE_ID = int(os.getenv("DEVICE_ID"), base=16)
SERIAL_NUMBER = os.getenv("SERIAL_NUMBER")
SYSTEM_VERSION = int(os.getenv("SYSTEM_VERSION"), base=16)
# --- Region and Language Information ---
COUNTRY_ID = int(os.getenv("COUNTRY_ID"))
COUNTRY_NAME = os.getenv("COUNTRY_NAME")
REGION_ID = int(os.getenv("REGION_ID"))
REGION_NAME = os.getenv("REGION_NAME")
LANGUAGE = os.getenv("LANGUAGE")
# --- Account Information ---
USERNAME = os.getenv("NNID_USERNAME")
PASSWORD = os.getenv("PASSWORD")

md_escape = {ord('*'): '\\*', ord('_'): '\\_', ord('~'): '\\~',
             ord('`'): '\\`', ord('>'): '\\>', ord('|'): '\\|'}


def mark_faster_time(record1: RankingRankData, record2: RankingRankData):
    if record1 is None:
        return "-:--.---"
    elif record2 is None or record1.score >= record2.score:
        return ts.format_time(record1.score)
    else:
        return "<%s>" % ts.format_time(record1.score)


class BotBoi(commands.Bot):
    def __init__(self):
        prefix = '!'
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=prefix, intents=intents)
        self.mk8_client = MK8Client()
        self.mk8_client.set_device(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION)
        self.mk8_client.set_locale(REGION_ID, REGION_NAME, COUNTRY_ID, COUNTRY_NAME, LANGUAGE)

    async def setup_hook(self):
        await self.add_cog(Commands(self))

    async def on_ready(self):
        await self.tree.sync()
        await self.mk8_client.login(USERNAME, PASSWORD)
        print("We up, boys!")


class Commands(commands.Cog):
    def __init__(self, bot: BotBoi):
        self.bot = bot

    @commands.hybrid_command(aliases=["mu"], description="Gets the matchup between two players given their NNIDs")
    async def matchup(self, ctx, nnid1: str, nnid2: str):
        embed = discord.Embed()
        embed.title = f"Generating matchup between {nnid1} and {nnid2}..."
        embed.description = "Please wait..."
        message = await ctx.reply(embed=embed)
        try:
            async with self.bot.mk8_client.backend_login() as bc:
                rc = RankingClient(bc)
                m = ts.get_matchup(*(await ts.get_timesheets(rc, [nnid1, nnid2])))
            p1 = m.p1_timesheet
            p2 = m.p2_timesheet
            embed.title = (f"{p1.mii_name} ({p1.nnid})   vs.   {p2.mii_name} ({p2.nnid})"
                           .translate(md_escape))

            # Bold the score for the player with the most wins
            p1_wins = f"**{m.p1_wins}**" if m.p1_wins > m.p2_wins else m.p1_wins
            p2_wins = f"**{m.p2_wins}**" if m.p1_wins < m.p2_wins else m.p2_wins
            embed.description = f"{p1_wins} – {m.ties} – {p2_wins}"

            tracks = list(p1.records.keys())
            p1_times = [
                mark_faster_time(t1, t2) for t1, t2 in zip(p1.records.values(), p2.records.values())
            ]
            p2_times = [
                mark_faster_time(t2, t1) for t1, t2 in zip(p1.records.values(), p2.records.values())
            ]

            categories = ["Nitro Tracks", "Retro Tracks", "DLC Tracks"]
            for i, cat in enumerate(categories):
                rows = "\n".join(
                    "%-4s    %10s    %10s" %
                    (tracks[i * 16 + x], p1_times[i * 16 + x].center(10), p2_times[i * 16 + x].center(10))
                    for x in range(16)
                )
                embed.add_field(name=cat, value=f"```{rows}```", inline=False)
        except (RMCError, RuntimeError) as e:
            embed.title = f"Failed to generate a matchup between {nnid1} and {nnid2}:"
            if e.__class__ is RMCError:
                self.handle_rmcerror(e, embed)
            else:
                embed.description = "Failed to fetch both timesheets; connection timed out."
        finally:
            await message.edit(embed=embed)

    @commands.hybrid_command(description="Gets stats")
    async def stats(self, ctx, abbr):
        if abbr.lower() == "all" or abbr == '*':
            embed = await self._aggregate_stats()
        else:
            embed = await self._individual_stats(abbr)
        await ctx.reply(embed=embed)

    async def _aggregate_stats(self):
        embed = discord.Embed()
        tracks = [track for track in MK8Tracks]
        try:
            async with self.bot.mk8_client.backend_login() as bc:
                rc = RankingClient(bc)
                result = await get_stats(rc, tracks)
        except RMCError as e:
            embed.title = f"Failed to fetch stats for all tracks:"
            self.handle_rmcerror(e, embed)
        else:
            embed.title = "Stats for all tracks:"
            total_records = sum(stat.num_records for stat in result.values())
            aggregate_time = sum(stat.sum_of_times for stat in result.values())
            worst_time = max(stat.worst_time for stat in result.values())
            average_time = sum(stat.average_time * stat.num_records / total_records
                               for stat in result.values())
            embed.add_field(name="Total Times", value=total_records)
            embed.add_field(name="Average Time", value=ts.format_time(average_time))
            embed.add_field(name="Sum of Uploaded Times", value=format_total_time(aggregate_time))
            embed.add_field(name="Slowest Time", value=ts.format_time(worst_time))
        return embed

    async def _individual_stats(self, abbr):
        embed = discord.Embed()
        try:
            track = MK8Tracks[abbr]
        except KeyError:
            embed.title = f"The abbreviation {abbr} is not a known track abbreviation"
            embed.description = "Please try again with a more commonly used abbreviation instead"
            return embed

        try:
            async with self.bot.mk8_client.backend_login() as bc:
                rc = RankingClient(bc)
                result = (await get_stats(rc, track))[track.abbr]
        except RMCError as e:
            embed.title = f"Failed to fetch stats for {track.fullname} ({track.abbr}):"
            self.handle_rmcerror(e, embed)
        else:
            embed.title = f"Stats for {track.fullname} ({track.abbr})"
            embed.add_field(name="Total Times", value=result.num_records)
            embed.add_field(name="Average Time", value=ts.format_time(result.average_time))
            embed.add_field(name="Sum of Uploaded Times", value=format_total_time(result.sum_of_times))
            embed.add_field(name="Slowest Time", value=ts.format_time(result.worst_time))
        return embed

    @commands.hybrid_command(aliases=["ts"], description="Gets the timesheet for the player with the given NNID")
    async def timesheet(self, ctx, nnid):
        embed = discord.Embed()
        embed.title = f"Fetching timesheet for {nnid}..."
        embed.description = "Please wait..."
        message = await ctx.reply(embed=embed)
        try:
            async with self.bot.mk8_client.backend_login() as bc:
                rc = RankingClient(bc)
                player_ts = await ts.get_timesheet(rc, nnid)
            ts_list = player_ts.to_string_array()
            name = player_ts.mii_name.translate(md_escape)

            embed.title = f"Timesheet for {name} ({nnid}):" if name else f"Timesheet for {nnid}:"
            embed.description = "Shows the track abbreviation, worldwide position*, and time for each track."

            for index, cup in enumerate(MK8Cups):
                cup_value = "\n".join(ts_list[index * 4 + x] for x in range(4))
                embed.add_field(name=f"{cup.name.title()} Cup", value=f"```{cup_value}```")

            for i in range(len(MK8Cups) - 2, 0, -2):
                embed.insert_field_at(index=i, name='\u200B', value='\u200B', inline=False)

            embed.set_footer(text="*Note that worldwide positions may be inaccurate due to hacked times and alts.")

        except (KeyError, RMCError, RuntimeError) as e:
            embed.title = f"Failed to fetch the timesheet for {nnid}:"
            if e.__class__ is KeyError:
                embed.description = f'The NNID "{nnid}" does not exist.'
            elif e.__class__ is RMCError:
                self.handle_rmcerror(e, embed)
            else:
                embed.description = "Connection timed out."

        finally:
            await message.edit(embed=embed)

    @commands.hybrid_command(description="Gets the ghost for the player with the given NNID on the given track")
    async def ghost(self, ctx, abbr, nnid):
        embed = discord.Embed()
        embed.title = f"Fetching ghost for {nnid} on {abbr}..."
        embed.description = "Please wait..."
        try:
            track = MK8Tracks[abbr]
        except KeyError:
            embed.title = f"Failed to fetch the ghost for {nnid} on {abbr}:"
            embed.description = (f"The abbreviation {abbr} is not a known track abbreviation; "
                                 f"please try again with a more commonly used abbreviation instead")
            await ctx.reply(embed=embed)
            return

        try:
            pid = await self.bot.mk8_client.nnas.get_pid(nnid)
        except KeyError:
            embed.title = f"Failed to fetch the ghost for {nnid} on {track.fullname} ({track.abbr}):"
            embed.description = f'The NNID "{nnid}" does not exist'
            await ctx.reply(embed=embed)
            return

        embed.title = f"Fetching ghost for {nnid} on {abbr}..."
        embed.description = "Please wait..."
        message = await ctx.reply(embed=embed)

        try:
            rankdata, response = await self._get_ghost(track, pid)
        except RMCError:
            embed.title = f"Failed to fetch the ghost for {nnid} on {track.fullname} ({track.abbr}):"
            embed.description = f'The NNID "{nnid}" has never set a time on this track'
            await message.edit(embed=embed)
            return

        mii_name = MK8PlayerInfo(rankdata.common_data).mii.mii_name
        try:
            lb_name = (await self.bot.mk8_client.nnas.get_mii(pid)).name
        except NNASError:
            lb_name = mii_name
        if response.error():
            embed.title = f"Failed to fetch the ghost for {nnid} on {track.fullname} ({track.abbr}):"
            embed.description = f"The NNID '{nnid}' has never set a time on"
            await message.edit(embed=embed)
        else:
            motion_raw = rankdata.groups[0]
            motion = bool(motion_raw)
            info = MK8GhostInfo(response.body, motion=motion)
            embed.title = (f"Ghost for {lb_name} ({nnid})\n"
                           f"on {track.fullname} ({track.abbr}):")
            embed.description = "Summary of the ghost data"

            embed.add_field(name='Time', value=format_time(rankdata.score))
            embed.add_field(name='Motion Controls', value=motion)
            embed.add_field(name='Mii Name', value=mii_name)
            embed.add_field(name='Rank', value=rankdata.rank)
            embed.add_field(name='', value='', inline=False)

            upload_timestamp = response.headers["Last-Modified"]
            embed.add_field(name='Uploaded', value=f'{upload_timestamp[:16]}\n{upload_timestamp[18:]}')
            embed.add_field(name='Set', value=f'{str(info.weekday.name[:3]).title()}, {info.day:02d} '
                                              f'{calendar.month_abbr[info.month]} {info.year}\n'
                                              f'{info.hour:02d}:{info.min:02d}:{info.sec:02d}')
            embed.add_field(name='', value='', inline=False)

            for i, lap in enumerate(info.lap_times, start=1):
                embed.add_field(name=f'Lap {i}', value=lap)
            embed.add_field(name='', value='', inline=False)

            embed.add_field(name='Character', value=str(info.character.name).replace('_', ' ').title())
            embed.add_field(name='Vehicle', value=str(info.vehicle_body.name).replace('_', ' ').title())
            embed.add_field(name='Tires', value=str(info.tire.name).replace('_', ' ').title())
            embed.add_field(name='Glider', value=str(info.glider.name).replace('_', ' ').title())

            mins = info.data[0x36D]
            secs = info.data[0x36E]
            ms = int.from_bytes(info.data[0x370:0x372], 'big')
            ghost_time = (60000 * mins) + (1000 * secs) + ms

            packet = bytearray(f'{response.version} {response.status_code} {response.status_name}'.encode('utf-8')
                               + b'\r\n')
            for header, value in response.headers.items():
                packet.extend(f'{header}: {value}\r\n'.encode('utf-8'))
            packet.extend(f'Custom-Info: PID={pid} Motion={motion}\r\n'.encode('utf-8'))
            packet.extend(b'\r\n')
            packet.extend(info.data)

            pkt = discord.File(io.BytesIO(packet), f'{pid} {ghost_time:06d} {motion_raw}.bin')
            dg = discord.File(io.BytesIO(info.generate_header() + info.data), info.generate_filename('dg'))
            await message.edit(embed=embed, attachments=[dg, pkt])

    async def _get_ghost(self, track, pid):
        order_param = RankingOrderParam()
        order_param.order_calc = RankingOrderCalc.STANDARD
        order_param.offset = 0
        order_param.count = 1

        async with self.bot.mk8_client.backend_login() as bc:
            rankings = await RankingClient(bc).get_ranking(RankingMode.SELF, track.value,
                                                           order_param, 0, pid)
            rankdata = rankings.data[0]

            store = datastore.DataStoreClient(bc)

            get_param = datastore.DataStorePrepareGetParam()
            get_param.persistence_target.owner_id = pid
            get_param.persistence_target.persistence_id = track - 16
            get_param.extra_data = ["WUP", str(REGION_ID), REGION_NAME,
                                    str(COUNTRY_ID), COUNTRY_NAME, ""]

            req_info = await store.prepare_get_object(get_param)
            headers = {header.key: header.value for header in req_info.headers}
            response = await http.get(req_info.url, headers=headers)

            return rankdata, response

    @staticmethod
    def handle_rmcerror(error, embed):
        if error.code() == 0x8068000B:
            embed.description = "Servers are currently under maintenance."


async def main():
    async with BotBoi() as bot:
        await bot.start(os.getenv("TOKEN"))

asyncio.run(main())
