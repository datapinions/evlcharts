import logging
from argparse import ArgumentParser
from pathlib import Path
import evlcharts.variables as var

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

    parser.add_argument(
        "--fips",
        type=str,
        nargs="+",
        help="Provide this as SSCCC for the state and county.",
    )

    parser.add_argument("-o", "--output", required=True, type=str, help="Output file.")

    parser.add_argument("input", help="Input file. The output of join.py.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    input_path = Path(args.input)
    output_path = Path(args.output)

    logger.info(f"Reading input file `{input_path}`")

    df = pd.read_csv(
        input_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    output_path.mkdir(parents=True, exist_ok=True)

    for fips in args.fips:
        state = fips[:2]
        county = fips[2:]

        # There are a handful of outliers where median income is
        # over $250,000. The Census Bureau codes these as 250,001.
        # We filter them out.
        df_county = df[
            (df["STATE"] == state)
            & (df["COUNTY"] == county)
            & (df[var.MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS] <= 250_000)
        ]

        logger.info(f"Writing to output file `{output_path}`")
        df_county.to_csv(output_path / f"{fips}.csv", index=False)


if __name__ == "__main__":
    main()
