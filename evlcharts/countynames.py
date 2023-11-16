import logging
from pathlib import Path

import pandas as pd

import evlcharts.variables as var
from evlcharts.loggingargparser import LoggingArgumentParser

logger = logging.getLogger(__name__)


def main():
    parser = LoggingArgumentParser(logger)

    parser.add_argument(
        "-o", "--output-file", required=True, help="Output file for results."
    )
    parser.add_argument("--vintage", type=int, default=2018)
    parser.add_argument(
        "cofips", nargs="+", type=str, help="5 digit FIPS codes of counties."
    )

    args = parser.parse_args()

    output_path = Path(args.output_file)

    df = pd.DataFrame(
        [
            {"FIPS": cofips, "NAME": var.cofips_name(cofips, args.vintage)}
            for cofips in args.cofips
        ]
    )

    output_path.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()
