"""Utility to do a sanity check on the site and find missing files."""

import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

logger = logging.getLogger(__name__)


def check_images(path: Path, expected_maps: int) -> int:
    err_count = 0

    for county_path in path.glob("*"):
        image_count = len(list(county_path.glob("*.png")))

        if image_count != expected_maps:
            print(
                f"Found {image_count} files in {county_path}; expected {expected_maps}"
            )
            err_count = err_count + 1

    return err_count


def check_charts(site_path: Path) -> int:
    chart_path = site_path / "images" / "impact_charts"

    return check_images(chart_path, 10)


def check_maps(site_path: Path) -> int:
    map_path = site_path / "images" / "coverage_maps"

    return check_images(map_path, 10)


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--log",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
        default="WARNING",
    )

    parser.add_argument("site", help="Site directory.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    site_path = Path(args.site)

    logger.info(f"Checking site at {site_path.absolute()}")

    err_count = check_charts(site_path)
    err_count = err_count + check_maps(site_path)

    if err_count != 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
