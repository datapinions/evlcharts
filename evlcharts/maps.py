import logging
from argparse import ArgumentParser
from pathlib import Path

import censusdis.data as ced
import matplotlib.pyplot as plt
import pandas as pd
from censusdis.datasets import ACS5, DECENNIAL_PUBLIC_LAW_94_171

logger = logging.getLogger(__name__)


ALTERNATE_MAP_YEARS = {
    # 2009: 2010,
}

ALTERNATE_DATA_SET = {2000: DECENNIAL_PUBLIC_LAW_94_171}

"""
A map for years for which there are not CB shapefiles available to the alternate years to get them for.
"""


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
        help="Provide this as SSCCC for the state and county.",
    )

    parser.add_argument("--start", type=int, default=2009, help="Year to start.")
    parser.add_argument("--end", type=int, default=2018, help="Year to end.")

    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        choices=["filing_rate", "threatened_rate", "judgement_rate"],
        default="filing_rate",
        help="What variable are we trying to predict?",
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

    state = args.fips[:2]
    county = args.fips[2:]

    df = pd.read_csv(
        input_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    output_path.mkdir(parents=True, exist_ok=True)

    for year in range(args.start, args.end + 1):
        map_year = ALTERNATE_MAP_YEARS.get(year, year)

        df_year = df[df["year"] == year]

        logger.info(
            f"Mapping {year} with {len(df_year.index)} rows with maps from {map_year}."
        )

        dataset = ALTERNATE_DATA_SET.get(map_year, ACS5)

        gdf_map_year = ced.download(
            dataset=dataset,
            vintage=map_year,
            download_variables=["NAME"],
            state=state,
            county=county,
            tract="*",
            with_geometry=True,
        )

        logger.info(f"Total tracts: {len(gdf_map_year.index)}")

        gdf_plot = gdf_map_year.merge(
            df_year[["STATE", "COUNTY", "TRACT", args.y_column]],
            on=["STATE", "COUNTY", "TRACT"],
        )

        logger.info(f"Merged tracts: {len(gdf_plot.index)}")

        fig, ax = plt.subplots(figsize=(3, 3))

        ax = gdf_map_year.plot(
            color="beige",
            linewidth=0,
            ax=ax,
            zorder=1,
        )

        if len(gdf_plot.index) > 0:
            ax = gdf_plot.plot(
                color="seagreen",
                linewidth=0,
                ax=ax,
                zorder=2,
            )

        ax = gdf_map_year.boundary.plot(
            color="#333333",
            linewidth=1,
            ax=ax,
            zorder=3,
        )

        ax.axis("off")

        ax.set_title(
            f"{year} Data Coverage\n{len(gdf_plot.index)} of {len(gdf_map_year.index)} tracts",
            fontsize=9,
        )

        fig.savefig(output_path / f"{year}.png")


if __name__ == "__main__":
    main()
