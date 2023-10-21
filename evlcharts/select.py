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

    parser.add_argument(
        "-s", "--state", required=True, type=str, help="State FIPS code, e.g. 34 for NJ"
    )
    parser.add_argument(
        "-c",
        "--county",
        required=True,
        type=str,
        help="County fips code, three digits with leading zeros.",
    )

    parser.add_argument("-o", "--output", required=True, type=str, help="Output file.")

    parser.add_argument("input", help="Input file. The output of join.py.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    state = args.state
    county = args.county
    input_path = Path(args.input)
    output_path = Path(args.output)

    logger.info(f"Reading input file `{input_path}`")

    df = pd.read_csv(
        input_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    df = df[(df["STATE"] == state) & (df["COUNTY"] == county)]

    logger.info(f"Writing to output file `{output_path}`")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path)


if __name__ == "__main__":
    main()
