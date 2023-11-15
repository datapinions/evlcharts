import logging
from pathlib import Path

import pandas as pd

from evlcharts.loggingargparser import LoggingArgumentParser

logger = logging.getLogger(__name__)


def load_county(county_path: Path) -> pd.DataFrame:
    county_fips = county_path.stem

    logger.info(f"Processing county {county_fips}")

    df = (
        pd.read_csv(county_path)
        .reset_index()
        .rename({"index": "DECILE"}, axis="columns")
    )
    df["COUNTY"] = county_fips

    feature_cols = [col for col in df.columns if col not in ["COUNTY", "DECILE"]]
    df = df[["COUNTY", "DECILE"] + feature_cols]

    return df


def large_impact(df: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [col for col in df.columns if col not in ["COUNTY", "DECILE"]]

    df_high = df.groupby("COUNTY")[feature_cols].max()
    df_low = df.groupby("COUNTY")[feature_cols].min()
    df_gap = df_high - df_low

    df_large = pd.concat(
        df_gap[df_gap[feature] > 5.0].nlargest(10, feature) for feature in feature_cols
    )

    large_fips = sorted(list(df_large.index.unique()))

    print(", ".join(large_fips))

    if True:
        print("LARGEST")
        print(df_gap.nlargest(10, "B25119_003E_2018"))
        print(df_gap.nlargest(10, "frac_B25003A_003E"))
        print(df_gap.nlargest(10, "frac_B25003B_003E"))

        print("SMALLEST")
        print(df_gap.nsmallest(10, "B25119_003E_2018"))
        print(df_gap.nsmallest(10, "frac_B25003A_003E"))
        print(df_gap.nsmallest(10, "frac_B25003B_003E"))


def main():
    parser = LoggingArgumentParser(logger)

    parser.add_argument(
        "-o", "--output", required=True, type=str, help="Output yaml file."
    )
    parser.add_argument("counties", nargs="+", help="Files created by rankbucket.py.")

    args = parser.parse_args()

    output_path = Path(args.output)

    df_all_counties = pd.concat(load_county(Path(county)) for county in args.counties)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    large_impact(df_all_counties)
    df_all_counties.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
