from typing import List
import pandas as pd


# From the population by race group https://api.census.gov/data/2018/acs/acs5/groups/B03002.html
GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE = "B03002"

TOTAL_POPULATION = "B03002_001E"
TOTAL_HISPANIC_OR_LATINO = "B03002_012E"

# From income by tenure group https://api.census.gov/data/2018/acs/acs5/groups/B25119.html
GROUP_MEDIAN_HOUSEHOLD_INCOME_BY_TENURE = "B25119"

MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS = "B25119_003E"


def x_cols(df: pd.DataFrame) -> List[str]:
    cols = [
        MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS,
    ] + [
        f"frac_{variable}"
        for variable in df.columns
        if variable.startswith(GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE)
        and variable != TOTAL_POPULATION
    ]

    return cols
