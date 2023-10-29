import logging
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--log",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
        default="WARNING",
    )

    parser.add_argument("-i", "--input", help="Input file. The output of join.py.")

    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        choices=["filing_rate", "threatened_rate", "judgement_rate"],
        default="filing_rate",
        help="What variable are we trying to predict?",
    )

    parser.add_argument("-t", "--threshold", type=int, default=10)

    parser.add_argument(
        "-f",
        "--fips",
        type=str,
        nargs="+",
        help="Provide this as SSCCC for the state and county.",
    )

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    input_path = Path(args.input)

    logger.info(f"Reading input file `{input_path}`")

    df = pd.read_csv(
        input_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    good_fips = []

    for fips in args.fips:
        state = fips[:2]
        county = fips[2:]

        df_county = df[
            (df["STATE"] == state)
            & (df["COUNTY"] == county)
            & ~df[args.y_column].isna()
        ]

        if len(df_county.index) < args.threshold:
            logger.info(f"Less than 10 rows for county fips {fips}")
        else:
            good_fips.append(fips)

    print(" ".join(good_fips))


if __name__ == "__main__":
    main()
