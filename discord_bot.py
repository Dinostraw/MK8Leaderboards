import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from mk8boards.mk8 import timesheet as ts
from mk8boards.mk8.mk8 import MK8Cups, abbr_aliases, MK8Tracks, MK8Client
from mk8boards.mk8.track_stats import get_stats, format_all_stats, stats_to_labeled_dict
from mk8boards.str_mappings import standardize_abbr

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# --- Device Information ---
DEVICE_ID = int(os.getenv("DEVICE_ID"), base=16)
SERIAL_NUMBER = os.getenv("SERIAL_NUMBER")
SYSTEM_VERSION = int(os.getenv("SYSTEM_VERSION"), base=16)
# --- Region and Language Information ---
COUNTRY_ID = int(os.getenv("REGION_ID"))
COUNTRY_NAME = os.getenv("COUNTRY_NAME")
REGION_ID = int(os.getenv("REGION_ID"))
REGION_NAME = os.getenv("REGION_NAME")
LANGUAGE = os.getenv("LANGUAGE")
# --- Account Information ---
USERNAME = os.getenv("NNID_USERNAME")
PASSWORD = os.getenv("PASSWORD")

mk8_client = MK8Client(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION, COUNTRY_ID, COUNTRY_NAME,
                       REGION_ID, REGION_NAME, LANGUAGE, USERNAME, PASSWORD)

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    await mk8_client.login()
    print("We up, boys!")


def mark_time_if_faster(record1, record2):
    if record1 is None:
        return "-:--.---"
    elif record2 is None or record1.score >= record2.score:
        return ts.format_time(record1.score)
    else:
        return "<%s>" % ts.format_time(record1.score)


@bot.command(aliases=["mu"], description="Gets the matchup between two players given their NNIDs")
async def matchup(ctx, nnid1, nnid2):
    embed = discord.Embed()
    embed.title = f"Generating matchup between {nnid1} and {nnid2}..."
    embed.description = "Please wait..."
    message = await ctx.reply(embed=embed)
    try:
        m = ts.get_matchup(*(await ts.get_timesheets(mk8_client, [nnid1, nnid2])))
        p1 = m.p1_timesheet
        p2 = m.p2_timesheet
        embed.title = f"{p1.mii_name} ({p1.nnid})   vs.   {p2.mii_name} ({p2.nnid})"

        # Bold the score for the player with the most wins
        p1_wins = f"**{m.p1_wins}**" if m.p1_wins > m.p2_wins else m.p1_wins
        p2_wins = f"**{m.p2_wins}**" if m.p1_wins < m.p2_wins else m.p2_wins
        embed.description = f"{p1_wins} – {m.ties} – {p2_wins}"

        tracks = list(p1.records.keys())
        p1_times = [
            mark_time_if_faster(t1, t2) for t1, t2 in zip(p1.records.values(), p2.records.values())
        ]
        p2_times = [
            mark_time_if_faster(t2, t1) for t1, t2 in zip(p1.records.values(), p2.records.values())
        ]

        categories = ["Nitro Tracks", "Retro Tracks", "DLC Tracks"]
        for i, cat in enumerate(categories):
            rows = "\n".join(
                "%-4s    %10s    %10s" %
                (tracks[i*16 + x], p1_times[i*16 + x].center(10), p2_times[i*16 + x].center(10))
                for x in range(16)
            )
            embed.add_field(name=cat, value=f"```{rows}```", inline=False)
    except RuntimeError:
        embed.title = f"Failed to generate a matchup between {nnid1} and {nnid2}:"
        embed.description = "Failed to fetch both timesheets; connection timed out."
    finally:
        await message.edit(embed=embed)


@bot.command(description="Gets stats")
async def stats(ctx, *args):
    embed = discord.Embed()
    if len(args) == 0:
        tracks = [track for track in MK8Tracks]
        embed.title = "Stats for al/l tracks:"
        embed.description = "```%s```" % format_all_stats((await get_stats(mk8_client, tracks)))
        await ctx.reply(embed=embed)
        return

    abbr = standardize_abbr(args[0])
    if abbr in abbr_aliases:
        track = abbr_aliases[abbr]
        embed.title = f"Stats for {track.fullname} ({track.abbr})"
        track_stats = stats_to_labeled_dict((await get_stats(mk8_client, track))[track.abbr])
        for stat, value in track_stats.items():
            embed.add_field(name=stat, value=value)
    else:
        embed.title = f"The abbreviation {abbr} is not a known track abbreviation"
        embed.description = "Please try again with a more commonly used abbreviation instead"
    await ctx.reply(embed=embed)


@bot.command(aliases=["ts"], description="Gets the timesheet for the player with the given NNID")
async def timesheet(ctx, nnid):
    embed = discord.Embed()
    embed.title = f"Fetching timesheet for {nnid}..."
    embed.description = "Please wait..."
    message = await ctx.reply(embed=embed)
    try:
        player_ts = await ts.get_timesheet(mk8_client, nnid)
        ts_list = player_ts.to_string_array()
        name = player_ts.mii_name

        embed.title = f"Timesheet for {name} ({nnid}):" if name else f"Timesheet for {nnid}:"
        embed.description = "Shows the track abbreviation, worldwide position*, and time for each track."

        for index, cup in enumerate(MK8Cups):
            cup_value = "\n".join(ts_list[index*4 + x] for x in range(4))
            embed.add_field(name=f"{cup.name.title()} Cup", value=f"```{cup_value}```")

        for i in range(len(MK8Cups)-2, 0, -2):
            embed.insert_field_at(index=i, name='\u200B', value='\u200B', inline=False)

        embed.set_footer(text="*Note that worldwide positions may be inaccurate due to hacked times and alts.")

    except KeyError as e:
        embed.title = f"Failed to fetch the timesheet for {nnid}:"
        if e.__class__ is KeyError:
            embed.description = f"The NNID \"{nnid}\" does not exist."
        else:
            embed.description = "Connection timed out."
    finally:
        await message.edit(embed=embed)


bot.run(os.getenv("TOKEN"))
