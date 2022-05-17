import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


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


def format_time(score):
    millisec = score % 1000
    seconds = score // 1000 % 60
    minutes = score // 1000 // 60
    return "%i:%02i.%03i" % (minutes, seconds, millisec)


def prevent_excel_reformat(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"'{x}")
    return df


def main():
    directory = "./Output/Boards/"
    filename = "62 WW 2022-05-17 00-59.csv"

    track_id, _, timestamp = filename.split(" ", maxsplit=2)
    timestamp = timestamp[:-4]

    df = pd.read_csv(directory + filename)
    print(df.shape)

    df_filtered = df[df["raw_time"] >= 102676]
    df_filtered["rank"] = df_filtered["rank"] - df.shape[0] + df_filtered.shape[0] + 1
    print(df_filtered["country"].unique(), "\n")
    print(df_filtered["country"].value_counts().to_string(), "\n")

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
    print(df_mo.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_mo, directory, track_id, " MO ", timestamp)
    df_to_xlsx(df_mo, directory, track_id, " MO ", timestamp, prevent_reformat=True,
               columns=prev_ref_cols)

    # American Regionals
    df_am = filter_boards(df_filtered, "country", am_set)[cols]
    print(df_am.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_am, directory, track_id, " AM ", timestamp)

    # European Regionals
    df_eu = filter_boards(df_filtered, "country", eu_set)[cols]
    print(df_eu.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_eu, directory, track_id, " EU ", timestamp)

    # Asian Regionals
    df_as = filter_boards(df_filtered, "country", as_set)[cols]
    print(df_as.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_as, directory, track_id, " AS ", timestamp)

    # Middle Eastern Regionals
    df_me = filter_boards(df_filtered, "country", me_set)[cols]
    print(df_me.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_me, directory, track_id, " ME ", timestamp)

    # African Regionals
    df_af = filter_boards(df_filtered, "country", af_set)[cols]
    print(df_af.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_af, directory, track_id, " AF ", timestamp)

    # Oceanian Regionals
    df_oc = filter_boards(df_filtered, "country", oc_set)[cols]
    print(df_oc.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_oc, directory, track_id, " OC ", timestamp)

    # Japanese Country Rankings
    df_jp = df_filtered[df_filtered["country"] == "JPN"][cols]
    print(df_jp.to_string(index=False, max_rows=50), "\n")
    df_to_csv(df_jp, directory, track_id, " JP ", timestamp)

    print(df_filtered[cols].tail(10).to_string(index=False))

    # avg_time_per_nat = df.groupby(["country"])["raw_time"].mean().sort_values()
    # avgs_formatted = avg_time_per_nat.apply(format_time)
    # print(avgs_formatted.to_string(header=False))
    #
    # ax = avg_time_per_nat.plot.bar(color=["deepskyblue", "royalblue"])
    # ax.set_yticks([0, 30000, 60000, 90000, 102676, 120000, 150000,
    #                180000, 210000, 240000, 270000, 30000])
    # ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_time(x)))
    # ax.axhline(y=102676, color="crimson", linewidth=3, label="WR")
    # plt.margins(0, 0)
    # plt.title("dCL Average Time per Country")
    # plt.grid(axis='y', linestyle='--', color="black")
    # plt.show()


if __name__ == "__main__":
    main()
