import logging
import sys
from argparse import BooleanOptionalAction
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import xgboost
import yaml
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import RandomizedSearchCV

import evlcharts.variables as var
from evlcharts.loggingargparser import LoggingArgumentParser

logger = logging.getLogger(__name__)


def optimize(
    df: pd.DataFrame,
    x_cols: Iterable[str],
    y_col: str,
    w_col: Optional[str] = None,
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
        "score": float(reg.best_estimator_.score(X, y)),
    }

    result["params"]["learning_rate"] = float(result["params"]["learning_rate"])
    result["params"]["subsample"] = float(result["params"]["subsample"])

    return result


def linreg(
    df: pd.DataFrame,
    x_cols: Iterable[str],
    y_col: str,
    w_col: Optional[str] = None,
) -> Dict[str, Any]:
    regressor = LinearRegression()

    if w_col is None:
        model = regressor.fit(df[x_cols], df[y_col])
        score = regressor.score(df[x_cols], df[y_col])
    else:
        model = regressor.fit(df[x_cols], df[y_col], sample_weight=df[w_col])
        score = regressor.score(df[x_cols], df[y_col], sample_weight=df[w_col])

    coefficients = model.coef_.tolist()
    intercept = model.intercept_

    return {
        "coefficients": coefficients,
        "intercept": float(intercept),
        "score": float(score),
    }


def main():
    parser = LoggingArgumentParser(logger)

    parser.add_argument(
        "--fips",
        type=str,
        required=True,
        help="Provide this as SSCCC for the state and county.",
    )

    parser.add_argument("--dry-run", action=BooleanOptionalAction)
    parser.add_argument(
        "-o", "--output", required=True, type=str, help="Output yaml file."
    )

    parser.add_argument(
        "--population",
        type=str,
        choices=["all", "renters"],
        default="renters",
        required=True,
        help="What do we base the population metrics on?",
    )

    parser.add_argument(
        "-y",
        "--y-column",
        type=str,
        choices=["filing_rate", "threatened_rate", "judgement_rate"],
        default="filing_rate",
        help="What variable are we trying to predict?",
    )

    parser.add_argument("data", help="Input data file. Typically from select.py.")

    args = parser.parse_args()

    renters_only = args.population == "renters"

    data_path = Path(args.data)
    output_path = Path(args.output)

    df = pd.read_csv(
        data_path, header=0, dtype={"STATE": str, "COUNTY": str, "TRACT": str}
    )

    x_cols = var.x_cols(df, renters_only)

    y_col = args.y_column

    logger.info(f"Input shape: {df.shape}")
    df = df.dropna(subset=[y_col])
    logger.info(f"Shape after dropna: {df.shape}")

    if len(df.index) == 0:
        logger.warning(f"After removing nan from {y_col}, no data is left.")
        sys, exit(1)

    logger.info(
        f"Range: {df[y_col].min()} - {df[y_col].max()}; mean: {df[y_col].mean()}"
    )

    if args.dry_run:
        return

    xgb_params = optimize(df, x_cols, y_col)

    logger.info(f"Writing to output file `{output_path}`")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"All X shape: {df.shape}")
    df = df.dropna(subset=x_cols)
    logger.info(f"Dropna X shape: {df.shape}")

    linreg_params = linreg(df, x_cols, y_col)

    params = {
        "fips": args.fips,
        "linreg": linreg_params,
        "xgb": xgb_params,
    }
    with open(output_path, "w") as f:
        yaml.dump(params, f, sort_keys=True)


if __name__ == "__main__":
    main()
