import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from mk8boards.common import MK8Tracks as Tracks
from mk8boards.mk8.timesheet import format_time

# Modify in between here =================================================================================
DIRECTORY = "../Output/Boards/"
FILENAME = "55 WW 2022-05-18 07-43.csv"
WR = 104298  # WR time (in milliseconds)
SG = 127868  # Staff Ghost time (in milliseconds)
# ========================================================================================================
LABELED_TIMES = {WR: "WR", SG: "SG"}


def df_to_csv(df, *args):
    df.to_csv(''.join(x for x in args) + ".csv",
              encoding="utf-8-sig", index=False)


def df_to_xlsx(df, *args, prevent_reformat=True, columns=None):
    columns = [] if None else columns
    if prevent_reformat:
        df = prevent_excel_reformat(df, columns)

    df.to_excel(''.join(x for x in args) + ".xlsx",
                encoding="utf-8-sig", index=False)


def filter_boards(df: pd.DataFrame, column, values):
    return df[df[column].isin(values)]


def prevent_excel_reformat(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"'{x}")
    return df


def tick_formatter(x, _):
    return LABELED_TIMES[x] if x in LABELED_TIMES else format_time(x)


def main():
    track_id, _, timestamp = FILENAME.split(" ", maxsplit=2)
    timestamp = timestamp[:-4]
    track_name = "Unknown Track"
    track_abbr = "???"
    for track in Tracks:
        if int(track_id) == track.id_:
            track_name = track.fullname
            track_abbr = track.abbr

    df = pd.read_csv(DIRECTORY + FILENAME)
    # print(df.shape)

    df_filtered = df[df["raw_time"] >= WR]
    df_filtered["rank"] = df_filtered["rank"] - df.shape[0] + df_filtered.shape[0] + 1
    # print(df_filtered["country"].unique(), "\n")
    # print(df_filtered["country"].value_counts().to_string(), "\n")

    cols = ["rank", "time", "motion", "country", "nnid", "name"]
    prev_ref_cols = ["time"]  # Columns to prevent Excel from reformatting

    am_set = {"AIA", "ATG", "ARG", "ABW", "BHS", "BRB", "BLZ", "BOL",
              "BRA", "VGB", "CAN", "CYM", "CHL", "COL", "CRI", "DMA",
              "DOM", "ECU", "SLV", "GUF", "GRD", "GLP", "GTM", "GUY",
              "HTI", "HND", "JAM", "MTQ", "MEX", "MSR", "ANT", "NIC",
              "PAN", "PRY", "PER", "KNA", "LCA", "VCT", "SUR", "TTO",
              "TCA", "USA", "URY", "VIR", "VEN"}

    eu_set = {"ALB", "AUT", "BEL", "BIH", "BGR", "HRV", "CYP", "CZE",
              "DNK", "EST", "FIN", "FRA", "DEU", "GRC", "HUN", "ISL",
              "IRL", "ITA", "LVA", "LIE", "LTU", "LUX", "MKD", "MLT",
              "MNE", "NLD", "NOR", "POL", "PRT", "ROU", "RUS", "SRB",
              "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "AZE"}

    as_set = {"JPN", "CYP", "RUS", "TUR", "AZE", "TWN", "KOR", "HKG",
              "MAC", "IDN", "SGP", "THA", "PHL", "MYS", "CHN", "ARE",
              "IND", "OMN", "QAT", "KWT", "SAU", "SYR", "BHR", "JOR"}

    me_set = {"CYP", "TUR", "ARE", "EGY", "OMN", "QAT", "KWT", "SAU",
              "SYR", "BHR", "JOR"}

    af_set = {"BWA", "LSO", "MOZ", "NAM", "ZAF", "SWZ", "ZMB", "ZWE",
              "MRT", "MLI", "NER", "TCD", "SDN", "ERI", "DJI", "SOM",
              "EGY"}

    oc_set = {"AUS", "NZL"}

    # Motion Controls Rankings
    df_mo = df_filtered[df_filtered["motion"]][cols].drop(columns="motion")
    # print(df_mo.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_mo, DIRECTORY, track_id, " MO ", timestamp)
    df_to_xlsx(df_mo, DIRECTORY, track_id, " MO ", timestamp, prevent_reformat=True,
               columns=prev_ref_cols)

    # American Regionals
    df_am = filter_boards(df_filtered, "country", am_set)[cols]
    # print(df_am.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_am, DIRECTORY, track_id, " AM ", timestamp)

    # European Regionals
    df_eu = filter_boards(df_filtered, "country", eu_set)[cols]
    # print(df_eu.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_eu, DIRECTORY, track_id, " EU ", timestamp)

    # Asian Regionals
    df_as = filter_boards(df_filtered, "country", as_set)[cols]
    # print(df_as.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_as, DIRECTORY, track_id, " AS ", timestamp)

    # Middle Eastern Regionals
    df_me = filter_boards(df_filtered, "country", me_set)[cols]
    # print(df_me.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_me, DIRECTORY, track_id, " ME ", timestamp)

    # African Regionals
    df_af = filter_boards(df_filtered, "country", af_set)[cols]
    # print(df_af.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_af, DIRECTORY, track_id, " AF ", timestamp)

    # Oceanian Regionals
    df_oc = filter_boards(df_filtered, "country", oc_set)[cols]
    # print(df_oc.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_oc, DIRECTORY, track_id, " OC ", timestamp)

    # Japanese Country Rankings
    df_jp = df_filtered[df_filtered["country"] == "JPN"][cols]
    # print(df_jp.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_jp, DIRECTORY, track_id, " JP ", timestamp)

    # ====================

    tick_values = [WR, 0, 30000, 60000, 90000, 120000, 150000,
                   180000, 210000, 240000, 270000, 300000]

    # Average Time per Country Plot
    avg_time_per_nat = df.groupby(["country"])["raw_time"].mean().sort_values()
    avgs_formatted = avg_time_per_nat.apply(format_time)
    print(avgs_formatted.to_string(header=False))

    ax = avg_time_per_nat.plot.bar(color=["deepskyblue", "royalblue"])
    ax.set_yticks(tick_values)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_time(x)))
    ax.axhline(y=WR, color="crimson", linewidth=3, label="WR")
    plt.margins(0, 0)
    plt.title(f"{track_name} Average Time per Country")
    plt.grid(axis='y', linestyle='--', color="black")
    plt.show()

    # Frequency That Each Unique Time Occurs
    time_counts = df_filtered["raw_time"].value_counts().reindex(index=range(0, 300000), fill_value=0)
    ax = time_counts.plot.line()
    ax.set_xticks(tick_values)
    ax.xaxis.set_major_formatter(FuncFormatter(tick_formatter))
    plt.margins(0, 0)
    plt.title("dIIO Frequency of Each Unique Time")
    plt.show()

    # Probability Distribution Approximation
    ax = df_filtered["raw_time"].plot.kde()
    ax.set_xticks(tick_values)
    ax.xaxis.set_major_formatter(FuncFormatter(tick_formatter))
    plt.margins(0, 0)
    plt.title(f"{track_name} Time Density")
    plt.show()

    # Distribution per Interval of Time
    ax = df_filtered["raw_time"].plot.hist(bins=300, figsize=(8, 4.5))
    ax.set_xlim(left=0, right=299999)
    ax.set_xticks(tick_values)
    ax.xaxis.set_major_formatter(FuncFormatter(tick_formatter))
    ax.tick_params(labelsize=6)
    ax.axvline(x=SG, color="crimson", linewidth=1, linestyle="--", label="SG")
    plt.margins(0, 0)
    plt.title(f"{track_name} Time Distribution")
    plt.savefig(f"../Output/Plots/{track_abbr} Time Distribution (1 sec).png",
                dpi=1200, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    main()
