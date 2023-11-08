#!/usr/bin/env sh

# This is how I build from a clean state.

# Divide up the data by county.
gmake -j 8 data

# Optimize and produce hyperparameters.
# No -j because optimization uses multiprocessing.
gmake params

# Plets
gmake -j 8 plots

# Maps for the site.
gmake -j 8 maps

# Top scoring
gmake top

# Make and check the site.
gmake check_site
