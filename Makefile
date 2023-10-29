
PYTHON = python3.11
LOGLEVEL = INFO

# Set to all or renters. This controls what goes into the X
# for our model fitting. If all, then the frac_* columns are
# fractions of the total population for each demographic. If
# renters, then the frac_* columns are fractions of the
# populations of renters for each demographic.
POPULATION := renters

# What are we trying to predict in the model?
# Options are filing_rate, threatened_rate, and judgement_rate.
PREDICTION_Y := filing_rate

# Five digit SSCCC state and county fips codes.

# These are the ones with the most census tracts of data
# from the Eviction Lab.
TOP_EVL_DATA_FIPS := \
48201 12086 32003 36047 42101 26163 12011 36081 24031 24005 \
48029 37119 25017 37183 12071 24033 26125 48141 36005 12099 \
36061 12057 13121 25009 25027 42091 39035 15003 12095 25025 \
25021 26099 24003 12127 13067 32031 25005 37081 12117 48215 \
12031 25013 48453 48491 53061 55079 33011 42045 42017 25023 \
\
12021 37067 21067 29189 48245 41067 12115 48303 49049 48167 \
49035 44007 53063 48355 45045 55133 12083 27053 12081 26049 \
26081 39049 48339 24021 12033 48061 48479 12009 24025 13089 \
13051 24027 33015 35049 36085 39155 23005 34023 48039 12053 \
12111 42029 12101 42003 42129 26161 13135 10003 48423 12091

# These are the ones from the list above with scores >= 0.5.
TOP_SCORE_FIPS := \
42045 42129 13089 55079 42003 34023 27053 42017 26081 13135 \
42091 36047 26161

BASE_FIPS := $(TOP_SCORE_FIPS)

# The data directory
DATA_DIR := ../evldata/data

# Dataset of vendor data joined with census data.
# This is what the evldata project builds for us.
JOINED_DATA := $(DATA_DIR)/evl_census.csv

# Filter out the ones that have no data for the given y.
FIPS := $(shell $(PYTHON) -m evlcharts.filterfips --log $(LOGLEVEL) -y $(PREDICTION_Y) -i $(JOINED_DATA) -f $(BASE_FIPS))

# Working director, for e.g. params.
WORKING_DIR := ./working
WORKING_DATA_DIR := $(WORKING_DIR)/data

# County level data files.
COUNTY_DATA := $(FIPS:%=$(WORKING_DATA_DIR)/%.csv)

# Parameters
PARAMS_DIR := $(WORKING_DIR)/$(POPULATION)/$(PREDICTION_Y)/params/xgb
PARAMS_YAML := $(FIPS:%=$(PARAMS_DIR)/xgb-params-%.yaml)

# File listing the FIPS codes with the top scores.
TOP_SCORING := $(PARAMS_DIR)/top_scores-$(POPULATION)-$(PREDICTION_Y).txt

# Plots
PLOT_DIR := ./plots/$(POPULATION)/$(PREDICTION_Y)
COUNTY_PLOT_DIRS = $(FIPS:%=$(PLOT_DIR)/%)

.PRECIOUS: $(PARAMS_YAML) $(COUNTY_DATA)

.PHONY: all top clean

all: $(COUNTY_PLOT_DIRS) $(TOP_SCORING)

clean:
	rm -rf $(WORKING_DIR) $(PLOT_DIR)

top: $(TOP_SCORING)

$(WORKING_DATA_DIR)/%.csv: $(JOINED_DATA)
	$(PYTHON) -m evlcharts.select --fips $(basename $(@F)) -o $(WORKING_DATA_DIR) $<

$(PARAMS_DIR)/xgb-params-%.yaml: $(WORKING_DATA_DIR)/%.csv
	$(PYTHON) -m evlcharts.optimize --log $(LOGLEVEL) --population $(POPULATION) -y $(PREDICTION_Y) --fips $(word 3,$(subst -, ,$(basename $(@F)))) -o $@ $<

$(TOP_SCORING): $(PARAMS_YAML)
	$(PYTHON) -m evlcharts.topscore --log $(LOGLEVEL) -o $@ $(PARAMS_YAML)

$(PLOT_DIR)/%: $(WORKING_DATA_DIR)/%.csv $(PARAMS_DIR)/xgb-params-%.yaml
	$(PYTHON) -m evlcharts.plot --log $(LOGLEVEL) --population $(POPULATION) -y $(PREDICTION_Y) -o $@ -p $(word 2,$^) --fips $(basename $(notdir $(word 1,$^))) $(word 1,$^)
	touch $@

# A rule to make requirements.txt. Not part of the normal data build
# process, but useful for maintenance if we add or update dependencies.
requirements.txt: pyproject.toml poetry.lock
	poetry export --without-hashes --format=requirements.txt > $@
