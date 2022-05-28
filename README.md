# MK8 Leaderboards  
Personal project dedicated to messing around with the Time Trial leaderboards in Mario Kart 8 (MK8) for the Wii U.
A fairly basic Discord bot to fetch data from the leaderboards has also been created and is also in active development.
Hopes are to incorporate Mario Kart 8 Deluxe (MK8DX) as well and perhaps base this on a website.
Makes major use of **Kinnay's [Nintendo Clients](https://github.com/kinnay/NintendoClients) package**.

**This project is in active development; everything is subject to change**  
Everything found within the current project is subject to drastic rewrites or changes.
Probably don't depend on this being a stable project or package any time soon.
This is more so a personal project than a serious package at the moment.
As was stated before, anything is subject to being rewritten and overhauled.  

### Example Scripts
Can be found in the `Samples` folder.
- **course_stats.py:** Gathers stats from the leaderboards for each course in the game and prints them to the console.
- **exploitboards.py:** Fetches an arbitrary amount of records from the leaderboards and saves the data as both a CSV
  and an XLSX file.
- **ghost.py:** Downloads the ghost data (and optionally the common data) for the record of the specified player on
  the specified course. A modification of
  [this example script](https://github.com/kinnay/NintendoClients/blob/master/examples/wiiu/mariokart.py)
  made by **Kinnay**.
- **mk8dxtest.py:** A broken, desperate, pitiful attempt at trying to make the long-dead guest account work for the
  MK8DX leaderboards. I have no idea why I even have this still, it literally doesn't work.
  But maybe it could work if genuine Nintendo Switch credentials were used and the script was modified...
- **more_stats.py:** In case `course_stats.py` wasn't enough stats;
  a basic script that uses Pandas and Matplotlib to gather and visualize additional stats and also divide up the data.
- **player_timesheet.py:** Fetches and prints a player's entire timesheet.
  A timesheet is a complete list of a player's current personal records across all courses in the game.

### Requirements
Can be found in `requirements.txt`.
- **Core Requirements** (required):
  - Python 3.8 or higher
  - anyio
  - anynet
  - discord.py
  - nintendoclients
  - python-dotenv


- **Optional Requirements** (only used in sample scripts at the moment):
  - matplotlib
  - pandas
