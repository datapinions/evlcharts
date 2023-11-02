from typing import List

import pandas as pd
from censusdis import data as ced
from censusdis.datasets import ACS5

# From the population by race group https://api.census.gov/data/2018/acs/acs5/groups/B03002.html
GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE = "B03002"

TOTAL_POPULATION = "B03002_001E"
TOTAL_HISPANIC_OR_LATINO = "B03002_012E"

GROUP_TENURE_PREFIX = "B25003"
VARIABLE_TOTAL_RENTERS = "B25003_003E"

# The counts of renters by race and ethicity are in different groups,
# one per ethnicity.
GROUP_TENURE_WHITE = "B25003A"
GROUP_TENURE_BLACK = "B25003B"
GROUP_TENURE_ASIAN = "B25003D"
GROUP_TENURE_HISPANIC_LATINO = "B25003I"

TENURE_BY_RACE_GROUPS = [
    GROUP_TENURE_WHITE,
    GROUP_TENURE_BLACK,
    GROUP_TENURE_ASIAN,
    GROUP_TENURE_HISPANIC_LATINO,
]

# From income by tenure group https://api.census.gov/data/2018/acs/acs5/groups/B25119.html
MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS = "B25119_003E"

# We want to use the feature we constructed that corrects all years to 2018 dollars.
MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS_2018_USD = (
    f"{MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS}_2018"
)


# Names of all of the features to use in labels on plots.
FEATURE_NAMES = {
    "frac_B03002_003E": "White Alone as Percentage of Overall Population",
    "frac_B03002_004E": "Black Alone as Percentage of Overall Population",
    "frac_B03002_005E": "American Indian or Alaskan Native Alone as Percentage of Overall Population",
    "frac_B03002_006E": "Asian Alone as Percentage of Overall Population",
    "frac_B03002_007E": "Native Hawaiian or Other Pacific Islander Alone as Percentage of Overall Population",
    "frac_B03002_008E": "Some Other Race Alone as Percentage of Overall Population",
    "frac_B03002_010E": "Two races Including Some Other Race as Percentage of Overall Population",
    "frac_B03002_011E": "Two races Excluding Some Other Race, or Three or More Races "
    "as Percentage of Overall Population",
    "frac_B03002_012E": "Hispanic or Latino of Any Race as Percentage of Overall Population",
    "frac_B25003A_003E": "White Alone as Percentage of Renters",
    "frac_B25003B_003E": "Black Alone as Percentage of Renters",
    "frac_B25003C_003E": "American Indian or Alaskan Native Alone as Percentage of Renters",
    "frac_B25003D_003E": "Asian Alone as Percentage of Renters",
    "frac_B25003E_003E": "Native Hawaiian or Other Pacific Islander Alone as Percentage of Renters",
    "frac_B25003F_003E": "Some Other Race Alone as Percentage of Renters",
    "frac_B25003G_003E": "Two races Including Some Other Race as Percentage of Renters",
    "frac_B25003H_003E": "Two races Excluding Some Other Race, or Three or More Races as Percentage of Renters",
    "frac_B25003I_003E": "Hispanic or Latino of any Race as Percentage of Renters",
    MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS_2018_USD: "Median Household Income for Renters - 2018 Dollars",
}


def x_cols(df: pd.DataFrame, renters_only: bool) -> List[str]:
    if renters_only:
        cols = [
            MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS_2018_USD,
        ] + [
            f"frac_{variable}"
            for variable in df.columns
            if variable.startswith(GROUP_TENURE_PREFIX)
            and variable != VARIABLE_TOTAL_RENTERS
        ]
    else:
        cols = [
            MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS_2018_USD,
        ] + [
            f"frac_{variable}"
            for variable in df.columns
            if variable.startswith(GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE)
            and variable != TOTAL_POPULATION
        ]

    return cols


def cofips_name(fips, year):
    state_fips = fips[:2]
    county_fips = fips[2:]

    # Get name of the county from the U.S. Census servers.
    df_county = ced.download(ACS5, year, ["NAME"], state=state_fips, county=county_fips)

    county_name = df_county["NAME"].iloc[0]
    return county_name
