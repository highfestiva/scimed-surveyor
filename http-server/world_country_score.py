from bokeh.models import ColorBar, GeoJSONDataSource, LinearColorMapper
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider
from functools import lru_cache
import json


@lru_cache
def load_countries():
    return json.load(open('data/countries.json'))


def plot_map(country_code2score):
    max_score = max(country_code2score.values())
    j = load_countries()
    features = []
    for feature in j['features']:
        cc = feature['properties']['country_code']
        score = country_code2score.get(cc)
        if score:
            feature['properties']['score'] = score
            features.append(feature)
    j['features'] = features
    json_str = json.dumps(j)
    geosource = GeoJSONDataSource(geojson=json_str)

    color_mapper = LinearColorMapper(palette='Turbo256', low=1, high=max_score)
    p = figure(x_range=(-18e6, 19e6), y_range=(-5e6, 11e6), tools='pan,box_zoom,wheel_zoom,reset', active_scroll='wheel_zoom', sizing_mode='stretch_both')
    p.toolbar.logo = None
    p.xaxis.visible = False
    p.yaxis.visible = False
    p.xgrid.visible = False
    p.ygrid.visible = False

    p.add_tile(get_provider('CARTODBPOSITRON'))

    p.patches('xs', 'ys', source=geosource, fill_alpha=0.7, line_width=0.5, line_color='#777777', fill_color = {'field': 'score', 'transform': color_mapper})

    color_bar = ColorBar(color_mapper=color_mapper, background_fill_alpha=0.7, border_line_color=None, location=(0,0), orientation='horizontal')
    p.add_layout(color_bar, 'below')
    return p
