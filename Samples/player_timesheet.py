import logging
import os

import anyio
from dotenv import load_dotenv

from mariokart8.mk8 import MK8Client
from mariokart8.timesheet import get_timesheet

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

# To get a player's timesheet, we need their Nintendo Network ID
PLAYER_NNID = "dorasa15"
# ----------------------------------


async def main():
    mk8_client = MK8Client(DEVICE_ID, SERIAL_NUMBER, SYSTEM_VERSION, COUNTRY_ID,
                           COUNTRY_NAME, REGION_ID, REGION_NAME, LANGUAGE,
                           USERNAME, PASSWORD)
    await mk8_client.login()
    for time in (await get_timesheet(mk8_client, PLAYER_NNID)).to_string_array():
        print(time)


if __name__ == "__main__":
    anyio.run(main)
    # input("Press Enter to exit...")
