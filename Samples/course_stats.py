import logging
import os

import anyio
from dotenv import load_dotenv
from nintendo.nex.ranking import RankingClient

from mk8boards.common import MK8Tracks as Tracks
from mk8boards.mk8.boards_client import MK8Client
from mk8boards.mk8.track_stats import format_all_stats, get_stats

logging.basicConfig(level=logging.INFO)

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


async def main():
    client = MK8Client()
    client.set_device(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION)
    client.set_locale(REGION_ID, REGION_NAME, COUNTRY_ID, COUNTRY_NAME, LANGUAGE)

    await client.login(USERNAME, PASSWORD)
    async with client.backend_login() as bc:
        rc = RankingClient(bc)
        stats = await get_stats(rc, [track for track in Tracks])

        ranks = {
            abbr: n for n, (abbr, _) in enumerate(sorted(stats.items(), reverse=True, key=lambda x: x[1].num_records),
                                                  start=1)
        }
        print("Rank | Track | Total Times")
        print("=" * 26)
        for abbr, tstats in stats.items():
            print(f"{int(ranks[abbr]):>4d} | {abbr:>5s} | {int(tstats.num_records):>11d}")

        stats = {k: v for k, v in sorted(stats.items(), key=lambda x: x[1].num_records)}
        print(format_all_stats(stats))


if __name__ == "__main__":
    anyio.run(main)
    # input("Press Enter to exit...")
