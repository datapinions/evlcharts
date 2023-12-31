import logging
from pathlib import Path

import pandas as pd
import yaml

from evlcharts.loggingargparser import LoggingArgumentParser

logger = logging.getLogger(__name__)


def main():
    parser = LoggingArgumentParser(logger)

    parser.add_argument(
        "--fips",
        type=str,
        nargs="+",
        help="Provide this as SSCCC for the state and county.",
    )

    parser.add_argument("-o", "--output", required=True, type=str, help="Output file.")

    parser.add_argument("params", nargs="+", help="Input parameter files")

    args = parser.parse_args()

    output_path = Path(args.output)

    scores = []

    for file in args.params:
        input_path = Path(file)
        logger.info(f"Reading input parameter file {input_path}")

        with open(file) as f:
            result = yaml.full_load(f)

        fips = result["fips"]
        xgb_score = result["xgb"]["score"]

        scores.append({"FIPS": fips, "SCORE": xgb_score})

    df_scores = pd.DataFrame(scores)

    df_scores.sort_values(by="SCORE", ascending=False, inplace=True)

    df_scores.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
