
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
06037 17031 04013 48201 36047 06073 26163 06059 48113 12086 \
39035 06065 32003 42101 53033 48439 48029 12011 36081 06071 \
06067 12099 12057 55079 27053 26125 36061 39049 06001 25017 \
12103 40109 51059 18097 39061 37119 47157 09003 04019 34013 \
24033 49035 17043 12095 48453 13121 29189 29095 21111 06019 \
\
26099 25025 09009 09001 11001 34003 40143 06075 34023 41051 \
12031 37183 25027 22071 34017 53053 25009 01073 06013 15003 \
47037 31055 35001 39113 12105 17097 48085 13089 53061 36005 \
06085 12071 34025 17197 27123 39153 08005 26049 08031 24510 \
44007 39095 10003 34007 48121 25005 34029 12101 20173 48141 \
\
26081 25021 08041 18089 06077 13067 37081 20091 01097 08059 \
06029 24005 06081 34005 13135 12009 29510 12127 34039 24031 \
47093 49049 25013 41067 55025 53011 51810 34031 34027 25023 \
19153 18003 53063 37067 08001 27037 48215 22033 32031 12115 \
06095 22051 39151 45045 41039 45079 12117 45019 27003 17089 \
\
51710 36085 51153 06107 47065 17201 39017 34021 24003 36103 \
41005 29183 26161 48355 48157 12081 39093 26065 21067 01089 \
51041 55133 06053 39099 18141 45063 13051 12033 34001 45051 \
31109 51760 20209 08069 48167 48303 12073 51087 29077 34015 \
23005 37071 06099 28049 34035 08123 06061 40027 01101 37051 \
\
12021 48027 12083 26077 39085 17163 41047 37063 26145 16001 \
45083 48061 48339 22017 39155 51107 54039 17119 37021 33011 \
17167 12069 17111 48491 12001 55009 51013 08013 25001 26139 \
26093 06087 10005 06007 18163 49011 49057 13063 02020 19163 \
01125 48309 17143 19113 27163 06097 39023 13021 23019 29047 \
\
45091 51700 26121 08101 27137 37129 55101 26147 34037 20177 \
08035 17019 01117 06089 51550 29099 28047 41029 55139 12005 \
12053 17161 45015 53067 31153 53035 53077 48423 26025 36119 \
55087 39025 45007 17113 37179 55105 12111 23031 48039 19013 \
12097 12091 26075 37097 25003 47165 51510 47125 24025 13117 \
\
39133 18095 18057 18157 35013 37025 45013 55059 06017 37001 \
33015 12015 18039 48441 13139 39103 26115 44003 24027 17115 \
39003 48041 37057 22055 51650 45041 24021 28033 39041 39089 \
10001 39057 45003 06111 34011 37147 25015 30111 37035 27109 \
06047 37031 53073 39165 51740 22019 26021 39139 01003 39169 \
\
47163 23011 37159 40031 37155 01055 34009 54011 17179 29019 \
19155 01015 17091 18167 12085 28059 40017 17099 18105 37019 \
06113 16027 23001 37151 39045 36059 51177 18127 18091 06055 \
12019 39173 18035 40131 45077 55073 01103 26045 34019 36067 \
54107 26017 51800 48381 13057 48139 51179 05119 08077 12061 \
\
37085 37133 37135 47187 18019 29021 19193 39007 47009 12087 \
36055 17183 34033 37191 48135 12017 55063 39029 53015 55131 \
13151 37089 37101 45035 06031 26005 21037 47149 54061 26087 \
55117 21227 26103 28121 34041 48209 09011 48329 19061 04025 \
26091 21059 24043 16055 19103 29097 51770 51085 01069 12055 \
\
13153 15001 23003 41019 48181 24013 01121 24017 01077 26037 \
39081 41017 48183 37045 37157 39109 47113 17037 41043 01081 \
39157 22109 53057 09005 20045 30013 36001 39055 48469 44005 \
13113 18067 27139 27145 55027 12113 13115 48479 55127 18081 \
33013 44009 55039 37171 40037 55035 41035 51003 15009 54033


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
SORTED_SCORING := $(PARAMS_DIR)/sorted_scores-$(POPULATION)-$(PREDICTION_Y).csv

# County name lookup.
COUNTY_NAMES := $(WORKING_DATA_DIR)/county_names.csv

# Plots
PLOT_ROOT := ./plots
PLOT_DIR := $(PLOT_ROOT)/$(POPULATION)/$(PREDICTION_Y)
COUNTY_PLOT_DIRS = $(FIPS:%=$(PLOT_DIR)/%)

# Bucketed impact dirs
BUCKETED_IMPACT_DIR := $(WORKING_DIR)/$(POPULATION)/$(PREDICTION_Y)/impact_buckets/xgb
COUNTY_IMPACT_BUCKETS := $(FIPS:%=$(BUCKETED_IMPACT_DIR)/%.csv)

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

.PHONY: all top site_html check_site data params maps plots impact_buckets rank_buckets county_names clean

all: $(COUNTY_PLOT_DIRS) $(SORTED_SCORING)

data: $(COUNTY_DATA)

params: $(PARAMS_YAML)

clean:
	-rm -rf $(WORKING_DIR) $(PLOT_ROOT)

top: $(SORTED_SCORING)

$(WORKING_DATA_DIR)/%.csv: $(JOINED_DATA)
	$(PYTHON) -m evlcharts.select --fips $(basename $(@F)) -o $(WORKING_DATA_DIR) $<

$(PARAMS_DIR)/xgb-params-%.yaml: $(WORKING_DATA_DIR)/%.csv
	$(PYTHON) -m evlcharts.optimize --log $(LOGLEVEL) --population $(POPULATION) -y $(PREDICTION_Y) --fips $(word 3,$(subst -, ,$(basename $(@F)))) -o $@ $<

$(SORTED_SCORING): $(PARAMS_YAML)
	$(PYTHON) -m evlcharts.topscore --log $(LOGLEVEL) -o $@ $(PARAMS_YAML)

$(PLOT_DIR)/% $(BUCKETED_IMPACT_DIR)/%.csv &: $(WORKING_DATA_DIR)/%.csv $(PARAMS_DIR)/xgb-params-%.yaml
	$(PYTHON) -m evlcharts.plot --log $(LOGLEVEL) --population $(POPULATION) -y $(PREDICTION_Y) \
    -o $(PLOT_DIR)/$* -p $(word 2,$^) --fips $* \
    --bucket $(BUCKETED_IMPACT_DIR)/$*.csv \
    $(word 1,$^)
	touch $@

plots: $(COUNTY_PLOT_DIRS)

impact_buckets: $(COUNTY_IMPACT_BUCKETS)

rank_buckets: $(BUCKETED_IMPACT_DIR)/summary/top.csv

$(BUCKETED_IMPACT_DIR)/summary/top.csv: $(COUNTY_IMPACT_BUCKETS)
	$(PYTHON) -m evlcharts.rankbuckets --log $(LOGLEVEL) -o $@ $^

# Rules to make maps indicating where we have coverage.
maps: $(COVERAGE_MAPS)

$(COVERAGE_MAPS_DIR)/%: $(WORKING_DATA_DIR)/%.csv
	$(PYTHON) -m evlcharts.maps --fips $(@F) -y $(PREDICTION_Y) -o $@ $<
	touch $@

county_names: $(COUNTY_NAMES)

$(COUNTY_NAMES):
	$(PYTHON) -m evlcharts.countynames --log $(LOGLEVEL) -o $@ $(BASE_FIPS)

# Rules to make the site.
site_html: $(SITE_HTML) $(SITE_IMAGE_DIR)/impact_charts $(COVERAGE_MAPS) $(SITE_IMAGE_DIR)/coverage_maps
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
$(SITE_DIR)/%.html: $(HTML_TEMPLATE_DIR)/%.html.j2 $(COUNTY_NAMES)
	mkdir -p $(@D)
	$(PYTHON) -m evlcharts.rendersite --log $(LOGLEVEL) -c $(SORTED_SCORING) -n $(COUNTY_NAMES) -o $@ $<

# A rule to make requirements.txt. Not part of the normal data build
# process, but useful for maintenance if we add or update dependencies.
requirements.txt: pyproject.toml poetry.lock
	poetry export --without-hashes --format=requirements.txt > $@
