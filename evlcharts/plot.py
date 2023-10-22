import logging
from typing import Iterable, Optional
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import xgboost
from sklearn.linear_model import LinearRegression
from censusdis.datasets import ACS5
from impactchart.model import XGBoostImpactModel
from matplotlib.ticker import FuncFormatter, PercentFormatter

import evlcharts.variables as var
import censusdis.data as ced


logger = logging.getLogger(__name__)


def xgb_score(df, x_cols, y_col, params) -> float:
    X = df[list(x_cols)]
    y = df[y_col]

    reg_xgb = xgboost.XGBRegressor(**params)

    model = reg_xgb.fit(X, y)

    score = model.score(X, y)

    return float(score)


def linreg_score(df, x_cols, y_col, coef, intercept) -> float:
    X = df[list(x_cols)]
    y = df[y_col]

    reg_linreg = _linreg_from_coefficients(coef, intercept)

    score = reg_linreg.score(X, y)

    return float(score)


def _linreg_from_coefficients(coef, intercept):
    reg_linreg = LinearRegression()
    # Instead of fitting, we are just going to kludge in
    # the known coefficients.
    reg_linreg.coef_ = np.array(coef)
    reg_linreg.intercept_ = intercept
    return reg_linreg


def _plot_id(feature, k, n, seed):
    return f"(f = {feature}; n = {n:,.0f}; k = {k}; s = {seed:08X})"

def plot_impact_chars(
        df,
        x_cols,
        y_col,
        year,
        params,
        output_path: Path,
        *,
        linreg: bool = False,
        linreg_coefs: Optional[Iterable[float]] = None,
        linreg_intercept: Optional[float] = None
):
    X = df[list(x_cols)]
    y = df[y_col]

    if linreg:
        reg_linreg = _linreg_from_coefficients(linreg_coefs, linreg_intercept)

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

    k = 50
    seed = 0x3423CDF1

    impact_model = XGBoostImpactModel(ensemble_size=k, random_state=seed, estimator_kwargs=params)
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

        # Plot the linear line by plotting the output of the linear
        # model with all other features zeroed out so they have no
        # effect.
        df_one_feature = pd.DataFrame(
            {f: X[f] if f == feature else 0.0 for f in X.columns}
        )

        if linreg:
            df_one_feature['impact'] = reg_linreg.predict(df_one_feature) - linreg_intercept

            ax = df_one_feature.plot(feature, 'impact', color="orange", ax=ax)

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

        plot_id = _plot_id(feature, k, len(df.index), seed)
        ax.text(
            0.99,
            0.01,
            plot_id,
            fontsize=8,
            backgroundcolor="white",
            horizontalalignment="right",
            verticalalignment="bottom",
            transform=ax.transAxes,
        )

        col_is_fractional = feature.startswith("frac_")

        if col_is_fractional:
            ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
            ax.set_xlim(-0.05, 1.05)
        else:
            ax.xaxis.set_major_formatter(dollar_formatter)
            ax.set_xlim(-5_000, 155_000)

        logger.info(f"Saving impact chart for {feature}.")
        fig.savefig(output_path / f"{feature}.jpg")


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
    parser.add_argument(
        "-p",
        "--parameters",
        required=True,
        type=str,
        help="Model parameters (from optimize.py).",
    )
    parser.add_argument("data", help="Input data file. Typically from select.py.")

    args = parser.parse_args()

    level = getattr(logging, args.log)

    logging.basicConfig(level=level)
    logger.setLevel(level)

    data_path = Path(args.data)
    output_path = Path(args.output)
    year = args.vintage

    df = pd.read_csv(
        data_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    with open(args.parameters) as f:
        result = yaml.full_load(f)

    xgb_params = result["xgb"]["params"]
    linreg_coefs = result["linreg"]["coefficients"]
    linreg_intercept = result["linreg"]["intercept"]

    x_cols = var.x_cols(df)
    y_col = "filing_rate"

    df = df.dropna(subset=list(x_cols + [y_col]))

    score_linreg = linreg_score(df, x_cols, y_col, result["linreg"]["coefficients"], result["linreg"]["intercept"])
    score_xgb = xgb_score(df, x_cols, y_col, xgb_params)

    logger.info(f'Linreg score: {score_linreg}')
    logger.info(f'Xgb score: {score_xgb}')

    output_path.mkdir(parents=True, exist_ok=True)
    plot_impact_chars(
        df, x_cols, y_col, year, xgb_params, output_path,
        linreg=False,
        linreg_coefs=linreg_coefs, linreg_intercept=linreg_intercept
    )


if __name__ == "__main__":
    main()
