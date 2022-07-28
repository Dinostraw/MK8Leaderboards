import logging
import os

import anyio
from dotenv import load_dotenv

from mk8boards.mk8.mk8 import MK8Client, MK8Tracks
from mk8boards.mk8.track_stats import format_all_stats, get_stats

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


async def main():
    mk8_client = MK8Client(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION, COUNTRY_ID,
                           COUNTRY_NAME, REGION_ID, REGION_NAME, LANGUAGE,
                           USERNAME, PASSWORD)
    await mk8_client.login()
    stats = await get_stats(mk8_client, [track for track in MK8Tracks])

    ranks = {stat[0]: n for n, stat in enumerate(sorted(stats.items(), reverse=True, key=lambda x: x[1][0]),
                                                 start=1)}
    print("Rank | Track | Total Times")
    print("=" * 26)
    for abbr, tstats in stats.items():
        print(f"{int(ranks[abbr]):>4d} | {abbr:>5s} | {int(tstats[0]):>11d}")

    stats = {k: v for k, v in sorted(stats.items(), key=lambda x: x[1][0])}
    print(format_all_stats(stats))


if __name__ == "__main__":
    anyio.run(main)
    # input("Press Enter to exit...")
