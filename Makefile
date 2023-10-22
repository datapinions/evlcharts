
PYTHON = python3.11
LOGLEVEL = INFO

# May want to override these to run for other counties.
# Georgia
STATE := 13
# DeKalb
COUNTY := 089


# The data directory
DATA_DIR := ../evldata/data

# Dataset of vendor data joined with census data.
# This is what the evldata project builds for us.
JOINED_DATA := $(DATA_DIR)/evl_census.csv

# Working director, for e.g. params.
WORKING_DIR := ./working
WORKING_DATA_DIR := $(WORKING_DIR)/data

# Just the desired county.
COUNTY_DATA := $(WORKING_DATA_DIR)/$(STATE)-$(COUNTY).csv

# Parameters
PARAMS_DIR := $(WORKING_DIR)/params/xgb
PARAMS_YAML := $(PARAMS_DIR)/xgb-params-$(STATE)-$(COUNTY).yaml

# Plots
PLOT_DIR := ./plots
COUNTY_PLOT_DIR = $(PLOT_DIR)/$(STATE)-$(COUNTY)

.PHONY: all clean

all: $(COUNTY_PLOT_DIR)

clean:
	rm -rf $(WORKING_DIR) $(PLOT_DIR)

$(COUNTY_DATA): $(JOINED_DATA)
	$(PYTHON) -m evlcharts.select -s $(STATE) -c $(COUNTY) -o $@ $<

$(PARAMS_YAML): $(COUNTY_DATA)
	$(PYTHON) -m evlcharts.optimize --log $(LOGLEVEL) -o $@ $<

$(COUNTY_PLOT_DIR): $(COUNTY_DATA) $(PARAMS_YAML)
	$(PYTHON) -m evlcharts.plot --log $(LOGLEVEL) -o $@ -p $(PARAMS_YAML) $(COUNTY_DATA)