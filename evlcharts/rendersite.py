import logging
from collections import defaultdict
from pathlib import Path

import jinja2
import pandas as pd

import evlcharts.variables as var
from evlcharts.loggingargparser import LoggingArgumentParser

logger = logging.getLogger(__name__)


def main():
    parser = LoggingArgumentParser(logger)

    parser.add_argument(
        "-o", "--output-file", required=True, help="Output file for results."
    )
    parser.add_argument(
        "-c",
        "--county-file",
        required=True,
        help="Top n list file we should render into template file.",
    )
    parser.add_argument(
        "-l", "--limit", type=int, help="Limit output to only this many counties."
    )
    parser.add_argument("template_file", help="Template file.")

    args = parser.parse_args()

    logger.info(f"Reading template from {args.template_file}")
    logger.info(f"Reading sorted county score data from {args.county_file}")

    df_all = pd.read_csv(args.county_file, dtype={"FIPS": str}).sort_values(
        by="SCORE", ascending=False
    )

    if args.limit is not None:
        df_all = df_all.iloc[: args.limit]

    df_all["NAME"] = df_all["FIPS"].apply(lambda cofips: var.cofips_name(cofips, 2018))

    df_all["STATE"] = df_all["NAME"].apply(
        lambda county_state: county_state.split(",")[-1].strip()
    )
    df_all["COUNTY"] = df_all["NAME"].apply(
        lambda county_state: county_state.split(",")[0].strip()
    )

    df_all.sort_values(by=["STATE", "COUNTY"], inplace=True)

    by_state = defaultdict(list)

    def _row_dict(row, omit_state: bool=True):
        row_dict = {
            "name": f"{row.NAME}",
            "fips": row.FIPS,
            "r2": f"{row.SCORE:.2f}",
        }

        if omit_state:
            row_dict['name'] = row_dict['name'].split(',')[0]

        return row_dict

    top_scores = [
        _row_dict(row, omit_state=False) for row in df_all.nlargest(25, 'SCORE').itertuples()
    ]

    bottom_scores = [
        _row_dict(row, omit_state=False) for row in df_all[df_all['SCORE'] <= 0.0].sort_values(by='SCORE').itertuples()
    ]

    for row in df_all.itertuples():
        by_state[row.STATE].append(_row_dict(row))

    template_args = dict(
        top_scores=top_scores,
        bottom_scores=bottom_scores,
        by_state=by_state,
        map_years=(2009, 2019),  # will use in range() in the template.
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
