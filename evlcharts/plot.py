import logging
from argparse import BooleanOptionalAction
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import xgboost
import yaml
from impactchart.model import XGBoostImpactModel
from matplotlib.ticker import FuncFormatter, PercentFormatter
from sklearn.linear_model import LinearRegression

import evlcharts.variables as var
from evlcharts.loggingargparser import LoggingArgumentParser

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
    impact_model: XGBoostImpactModel,
    X: pd.DataFrame,
    y_col,
    output_path: Path,
    county_name: str,
    k: int,
    seed: int,
    *,
    linreg: bool = False,
    linreg_coefs: Optional[Iterable[float]] = None,
    linreg_intercept: Optional[float] = None,
):
    if linreg:
        reg_linreg = _linreg_from_coefficients(linreg_coefs, linreg_intercept)

    impact_charts = impact_model.impact_charts(
        X,
        X.columns,
        subplots_kwargs=dict(
            figsize=(12, 8),
        ),
        feature_names=var.FEATURE_NAMES,
        y_name="Eviction " + y_col.replace("_", " ").title(),
        subtitle=county_name,
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
            df_one_feature["impact"] = reg_linreg.predict(df_one_feature)

            df_endpoints = pd.concat(
                [
                    df_one_feature.nsmallest(1, feature),
                    df_one_feature.nlargest(1, feature),
                ]
            )

            ax = df_endpoints.plot.line(
                feature, "impact", color="orange", ax=ax, label="Linear Model"
            )

        plot_id = _plot_id(feature, k, len(X.index), seed)
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
            ax.set_xlim(-5_000, max(10_000, df_one_feature[feature].max()) * 1.05)

        ax.grid(visible=True)

        feature_name = var.FEATURE_NAMES[feature]

        logger.info(f"Saving impact chart for {feature_name}.")
        fig.savefig(output_path / f"{feature_name.replace(' ', '-')}.png")


def main():
    parser = LoggingArgumentParser(logger)

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

    parser.add_argument(
        "--fips", type=str, help="Provide this as SSCCC for the state and county."
    )

    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        choices=["filing_rate", "threatened_rate", "judgement_rate"],
        default="filing_rate",
        help="What variable are we trying to predict?",
    )

    parser.add_argument(
        "--population",
        type=str,
        choices=["all", "renters"],
        default="renters",
        required=True,
        help="What do we base the population metrics on?",
    )

    parser.add_argument("--linreg", action="store_true")

    parser.add_argument("--bucket", help="Where to write bucket impact analysis.")

    parser.add_argument("data", help="Input data file. Typically from select.py.")

    args = parser.parse_args()

    fips = args.fips
    year = args.vintage

    county_name = var.cofips_name(fips, year)

    data_path = Path(args.data)
    output_path = Path(args.output)

    renters_only = args.population == "renters"

    df = pd.read_csv(
        data_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    with open(args.parameters) as f:
        result = yaml.full_load(f)

    xgb_params = result["xgb"]["params"]
    linreg_coefs = result["linreg"]["coefficients"]
    linreg_intercept = result["linreg"]["intercept"]

    x_cols = var.x_cols(df, renters_only)
    y_col = args.y_column

    df = df.dropna(subset=list(x_cols + [y_col]))

    score_linreg = linreg_score(
        df,
        x_cols,
        y_col,
        result["linreg"]["coefficients"],
        result["linreg"]["intercept"],
    )
    score_xgb = xgb_score(df, x_cols, y_col, xgb_params)

    logger.info(f"Linreg score: {score_linreg}")
    logger.info(f"Xgb score: {score_xgb}")

    output_path.mkdir(parents=True, exist_ok=True)

    X = df[list(x_cols)]
    y = df[y_col]

    k = 50
    seed = 0x3423CDF1

    impact_model = XGBoostImpactModel(
        ensemble_size=k, random_state=seed, estimator_kwargs=xgb_params
    )
    impact_model.fit(X, y)

    plot_impact_chars(
        impact_model,
        X,
        y_col,
        output_path,
        county_name=county_name,
        k=k,
        seed=seed,
        linreg=args.linreg,
        linreg_coefs=linreg_coefs,
        linreg_intercept=linreg_intercept,
    )

    if args.bucket is not None:
        logging.info("Computing bucketed impact.")

        df_bucketed_impact = pd.concat(
            (
                impact_model.bucketed_impact(X, feature)[["impact"]].rename(
                    {"impact": feature}, axis="columns"
                )
                for feature in x_cols
            ),
            axis="columns",
        )

        bucketed_path = Path(args.bucket)
        bucketed_path.parent.mkdir(parents=True, exist_ok=True)
        df_bucketed_impact.to_csv(bucketed_path, index=False)


if __name__ == "__main__":
    main()
