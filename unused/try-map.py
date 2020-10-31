#!/usr/bin/env python3

from bokeh.io import show
from world_country_score import plot_map

p = plot_map({'SWE':10, 'NLD':70, 'DNK':90})
show(p)
