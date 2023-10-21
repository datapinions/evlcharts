import logging
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import censusdis.data as ced
import pandas as pd
import xgboost
import yaml
from censusdis.datasets import ACS5
from impactchart.model import XGBoostImpactModel
from matplotlib.ticker import FuncFormatter, PercentFormatter
from scipy import stats
from sklearn.model_selection import RandomizedSearchCV

import evlcharts.variables as var

logger = logging.getLogger(__name__)


def optimize(
    year: int,
    df: pd.DataFrame,
    x_cols: Iterable[str],
    y_col: str,
    w_cols: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    reg_xgb = xgboost.XGBRegressor()

    param_dist = {
        "n_estimators": stats.randint(10, 100),
        "learning_rate": stats.uniform(0.01, 0.07),
        "subsample": stats.uniform(0.3, 0.7),
        "max_depth": stats.randint(2, 6),
        "min_child_weight": stats.randint(1, 4),
    }

    reg = RandomizedSearchCV(
        reg_xgb,
        param_distributions=param_dist,
        n_iter=200,
        error_score=0,
        n_jobs=-1,
        verbose=1,
        random_state=17,
    )

    X = df[list(x_cols)]
    y = df[y_col]

    reg.fit(X, y)

    result = {
        "params": reg.best_params_,
        "target": float(reg.best_score_),
    }

    result["params"]["learning_rate"] = float(result["params"]["learning_rate"])

    # Build impact charts.

    all_variables = pd.concat(
        [
            ced.variables.all_variables(
                ACS5, year, var.GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE
            ),
            ced.variables.all_variables(
                ACS5, year, var.GROUP_MEDIAN_HOUSEHOLD_INCOME_BY_TENURE
            ),
        ]
    )

    impact_model = XGBoostImpactModel(estimator_kwargs=result["params"])

    impact_model.fit(X, y)

    impact_charts = impact_model.impact_charts(
        X,
        X.columns,
        subplots_kwargs=dict(
            figsize=(12, 8),
        ),
    )

    dollar_formatter = FuncFormatter(
        lambda d, pos: f"\\${d:,.0f}" if d >= 0 else f"(\\${-d:,.0f})"
    )

    for feature, (fig, ax) in impact_charts.items():
        feature_base = feature.replace("frac_", "")

        label = all_variables[all_variables["VARIABLE"] == feature_base]["LABEL"].iloc[
            0
        ]
        label = label.split("!!")[-1]

        impacted = y_col.replace("_", " ").title()

        ax.grid()
        ax.set_title(f"Impact of {label} on {impacted}")
        ax.set_xlabel(label)
        ax.set_ylabel("Impact")

        col_is_fractional = feature.startswith("frac_")

        if col_is_fractional:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        else:
            ax.xaxis.set_major_formatter(dollar_formatter)

        logger.info(f"Saving impact chart for {feature}.")
        fig.savefig(Path("/var/tmp") / f"{feature}.jpg")

    return result


def main():
    parser = ArgumentParser()

    parser.add_argument(
        "--log",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level.",
        default="WARNING",
    )

    parser.add_argument("--dry-run", action=BooleanOptionalAction)
    parser.add_argument(
        "-o", "--output", required=True, type=str, help="Output yaml file."
    )
    parser.add_argument(
        "-v", "--vintage", default=2018, type=int, help="Year to get data."
    )
    parser.add_argument("data", help="Input data file. Typically from select.py.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    data_path = Path(args.data)
    output_path = Path(args.output)

    df = pd.read_csv(
        data_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    x_cols = [
        var.MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS,
    ] + [
        f"frac_{variable}"
        for variable in df.columns
        if variable.startswith(var.GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE)
        and variable != var.TOTAL_POPULATION
    ]

    y_col = "filing_rate"

    logger.info(f"Input shape: {df.shape}")
    df = df.dropna(subset=[y_col])
    logger.info(f"Shape after dropna: {df.shape}")

    logger.info(
        f"Range: {df[y_col].min()} - {df[y_col].max()}; mean: {df[y_col].mean()}"
    )

    if args.dry_run:
        return

    year = args.vintage

    params = optimize(year, df, x_cols, y_col)

    logger.info(f"Writing to output file `{output_path}`")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(params, f, sort_keys=True)


if __name__ == "__main__":
    main()
