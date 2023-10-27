from typing import List
import pandas as pd


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
    GROUP_TENURE_HISPANIC_LATINO
]

# From income by tenure group https://api.census.gov/data/2018/acs/acs5/groups/B25119.html
GROUP_MEDIAN_HOUSEHOLD_INCOME_BY_TENURE = "B25119"

MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS = "B25119_003E"

# Names of all of the features to use in labels on plots.
FEATURE_NAMES = {
    'frac_B03002_003E': 'White Alone',
    'frac_B03002_004E': 'Black Alone',
    'frac_B03002_005E': 'American Indian or Alaskan Native Alone',
    'frac_B03002_006E': 'Asian Alone',
    'frac_B03002_007E': 'Native Hawaiian or Other Pacific Islander Alone',
    'frac_B03002_008E': 'Some Other Race Alone',
    'frac_B03002_010E': 'Two races Including Some Other Race',
    'frac_B03002_011E': 'Two races Excluding Some Other Race, or Three or More Races',
    'frac_B03002_012E': 'Hispanic or Latino of Any Race',

    'frac_B25003A_003E': 'White Alone',
    'frac_B25003B_003E': 'Black Alone',
    'frac_B25003C_003E': 'American Indian or Alaskan Native Alone',
    'frac_B25003D_003E': 'Asian Alone',
    'frac_B25003E_003E': 'Native Hawaiian or Other Pacific Islander Alone',
    'frac_B25003F_003E': 'Some Other Race Alone',
    'frac_B25003G_003E': 'Two races Including Some Other Race',
    'frac_B25003H_003E': 'Two races Excluding Some Other Race, or Three or More Races',
    'frac_B25003I_003E': 'Hispanic or Latino of any Race',

    MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS: 'Median Household Income for Renters',
}

def x_cols(df: pd.DataFrame, renters_only: bool) -> List[str]:
    if renters_only:
        cols = [
                   MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS,
               ] + [
                   f"frac_{variable}"
                   for variable in  df.columns
                   if variable.startswith(GROUP_TENURE_PREFIX)
                      and variable != VARIABLE_TOTAL_RENTERS
               ]
    else:
        cols = [
            MEDIAN_HOUSEHOLD_INCOME_FOR_RENTERS,
        ] + [
            f"frac_{variable}"
            for variable in df.columns
            if variable.startswith(GROUP_HISPANIC_OR_LATINO_ORIGIN_BY_RACE)
            and variable != TOTAL_POPULATION
        ]

    return cols
