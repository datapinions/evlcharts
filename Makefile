
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
# from the Eviction Lab for 2009 and later.
TOP_EVL_DATA_FIPS := \
36047 26163 12086 32003 48029 12011 26125 48201 36061 42101 \
12095 26099 12057 37119 36081 12071 15003 37183 25009 39035 \
48453 26049 25027 27053 24005 39049 26081 48141 24031 44007 \
24033 13121 29189 25021 12099 34023 25005 12117 53061 25013 \
13067 12101 12127 37067 45045 51059 32031 37081 25017 24003 \
\
25023 26065 53053 48355 48167 48303 23005 12115 53063 35001 \
12021 12083 12081 48215 26161 34025 12033 48339 21067 33011 \
48491 48113 26145 41051 51153 39155 25025 13051 49049 36085 \
55133 23019 48121 26139 26077 49035 12053 53067 48423 27003 \
45083 34027 51107 26093 36005 12111 23031 48039 37097 41067 \
\
26147 27137 17161 27037 48439 26025 53077 12031 53035 33015 \
34017 37021 12091 17089 44003 48041 37057 51013 51087 24025 \
53011 12015 39023 13117 23011 31055 24027 12009 39093 23001 \
25001 12019 48441 24021 26021 27123 39103 48381 26115 48139 \
41039 27163 45091 12087 48135 37031 12103 13089 13135 12061 \
\
13139 48329 39061 13021 20091 45019 23003 12085 48061 39173 \
48181 34039 48183 12017 27109 26103 39099 53073 24013 35013 \
12113 33013 48187 24043 39013 21111 49011 49057 15001 29095 \
21037 18057 26091 48251 24017 27139 35045 19013 21227 51177 \
10005 39041 13095 44005 37127 19163 35049 39133 19113 34003


# These are the ones from the list above with scores >= 0.5.
TOP_SCORE_FIPS := \
42045 42129 13089 55079 42003 34023 27053 42017 26081 13135 \
42091 36047 26161

# Which one do we actually want to use?
BASE_FIPS := $(TOP_EVL_DATA_FIPS)
#BASE_FIPS := $(TOP_SCORE_FIPS)

# The data directory
DATA_DIR := ../evldata/data

# Dataset of vendor data joined with census data.
# This is what the evldata project builds for us.
JOINED_DATA := $(DATA_DIR)/evl_census.csv

# Filter out the ones that have no data for the given y.
MIN_DATA := 200
FIPS := $(shell $(PYTHON) -m evlcharts.filterfips --log WARNING -t $(MIN_DATA) -y $(PREDICTION_Y) -i $(JOINED_DATA) -f $(BASE_FIPS))

# Working director, for e.g. params.
WORKING_DIR := ./working
WORKING_DATA_DIR := $(WORKING_DIR)/data

# County level data files.
COUNTY_DATA := $(FIPS:%=$(WORKING_DATA_DIR)/%.csv)

# Parameters
PARAMS_DIR := $(WORKING_DIR)/$(POPULATION)/$(PREDICTION_Y)/params/xgb
PARAMS_YAML := $(FIPS:%=$(PARAMS_DIR)/xgb-params-%.yaml)

# File listing the FIPS codes with the top scores.
TOP_SCORING := $(PARAMS_DIR)/top_scores-$(POPULATION)-$(PREDICTION_Y).csv

# Plots
PLOT_DIR := ./plots/$(POPULATION)/$(PREDICTION_Y)
COUNTY_PLOT_DIRS = $(FIPS:%=$(PLOT_DIR)/%)

# Coverage maps.
COVERAGE_MAPS_DIR := $(WORKING_DIR)/maps/$(PREDICTION_Y)
COVERAGE_MAPS := $(FIPS:%=$(COVERAGE_MAPS_DIR)/%)

.PRECIOUS: $(PARAMS_YAML) $(COUNTY_DATA)

# Templates and related details for rendering the site.
HTML_TEMPLATE_DIR := ./templates
STATIC_HTML_DIR := ./static-html
SITE_DIR := $(WORKING_DIR)/site
SITE_IMAGE_DIR := $(SITE_DIR)/images

HTML_NAMES := index.html
SITE_HTML := $(HTML_NAMES:%=$(SITE_DIR)/%)
HTML_TEMPLATES := $(HTML_NAMES:%.html=$(HTML_TEMPLATE_DIR)/%.html.j2)

.PHONY: all top site_html check_site data params maps clean

all: $(COUNTY_PLOT_DIRS) $(TOP_SCORING)

data: $(COUNTY_DATA)

params: $(PARAMS_YAML)

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

# Rules to make maps indicating where we have coverage.
maps: $(COVERAGE_MAPS)

$(COVERAGE_MAPS_DIR)/%: $(WORKING_DATA_DIR)/%.csv
	$(PYTHON) -m evlcharts.maps --fips $(@F) -y $(PREDICTION_Y) -o $@ $<
	touch $@

# Rules to make the site.
site_html: $(SITE_HTML) $(SITE_PLOTS) $(SITE_IMAGE_DIR)/impact_charts $(COVERAGE_MAPS) $(SITE_IMAGE_DIR)/coverage_maps
	cp -r $(STATIC_HTML_DIR)/* $(SITE_DIR)

check_site: site_html
	$(PYTHON) -m evlcharts.checksite --log $(LOGLEVEL) $(SITE_DIR)

$(SITE_IMAGE_DIR)/impact_charts: $(COUNTY_PLOT_DIRS)
	-rm -rf $@
	mkdir -p $@
	cp -r $(COUNTY_PLOT_DIRS) $@

$(SITE_IMAGE_DIR)/coverage_maps: $(COVERAGE_MAPS_DIR)
	-rm -rf $@
	cp -r $< $@

# How to render and HTML template for the site.
$(SITE_DIR)/%.html: $(HTML_TEMPLATE_DIR)/%.html.j2
	mkdir -p $(@D)
	$(PYTHON) -m evlcharts.rendersite --log $(LOGLEVEL) -t $(TOP_SCORING) -o $@ $<

# A rule to make requirements.txt. Not part of the normal data build
# process, but useful for maintenance if we add or update dependencies.
requirements.txt: pyproject.toml poetry.lock
	poetry export --without-hashes --format=requirements.txt > $@
