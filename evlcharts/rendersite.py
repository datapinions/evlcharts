import logging
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

import jinja2
import pandas as pd

import evlcharts.variables as var

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
        "-o", "--output-file", required=True, help="Output file for results."
    )
    parser.add_argument(
        "-t",
        "--top-n-file",
        required=True,
        help="Top n list file we should render into template file.",
    )
    parser.add_argument(
        "-l", "--limit", type=int, help="Limit output to only this many counties."
    )
    parser.add_argument("template_file", help="Template file.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    logger.info(f"Reading template from {args.template_file}")
    logger.info(f"Reading top n data from {args.top_n_file}")

    df_top = pd.read_csv(args.top_n_file, dtype={"FIPS": str}).sort_values(
        by="SCORE", ascending=False
    )

    if args.limit is not None:
        df_top = df_top.iloc[: args.limit]

    df_top["NAME"] = df_top["FIPS"].apply(lambda cofips: var.cofips_name(cofips, 2018))

    df_top["STATE"] = df_top["NAME"].apply(
        lambda county_state: county_state.split(",")[-1].strip()
    )
    df_top["COUNTY"] = df_top["NAME"].apply(
        lambda county_state: county_state.split(",")[0].strip()
    )

    df_top.sort_values(by=["STATE", "COUNTY"], inplace=True)

    top_n_by_state = defaultdict(list)

    for row in df_top.itertuples():
        top_n_by_state[row.STATE].append(
            {
                "name": row.COUNTY,
                "image": f"./images/impact_charts/{row.FIPS}",
                "r2": f"{row.SCORE:.2f}",
            }
        )

    template_args = dict(
        top_n=top_n_by_state,
    )

    searchpath = Path(__file__).absolute().parent.parent

    template_loader = jinja2.FileSystemLoader(searchpath)
    template_env = jinja2.Environment(loader=template_loader, autoescape=True)
    template = template_env.get_template(args.template_file)

    rendered_text = template.render(template_args)

    with open(args.output_file, "w") as f:
        f.write(rendered_text)


if __name__ == "__main__":
    main()
