#!/usr/bin/env python3

import bokeh
from bokeh.embed import components as plot_html
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, WheelZoomTool
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.plotting import figure
from collections import defaultdict
from dateutil import parser as date_parser
from flask import Flask, request, render_template, send_from_directory
from elasticsearch import Elasticsearch


max_hits = 1000 # number of ES documents to return at most
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'vgr.ico', mimetype='image/x-icon')


@app.route('/covid-19')
def index():
    plot_html = plot('pubtator-covid-19', request.args)
    return render_template('covid-19-research.html', bokeh_version=bokeh.__version__, plot=plot_html)


def plot(index, args):
    print(args)
    todo: search on 'AND'.join(args), like...
    data = defaultdict(int)
    ss = es.search(index=index, size=max_hits)
    categories = defaultdict(lambda: defaultdict(int))
    for r in ss['hits']['hits']:
        s = r['_source']
        if s['date']:
            data[s['date']] += 1
        for k,v in s.items():
            if k not in ('date','title'):
                for label in v:
                    categories[k][label] += 1

    series = sorted([(date_parser.isoparse(t),cnt) for t,cnt in data.items()])
    x = [t for t,cnt in series]
    y = [cnt for t,cnt in series]

    cat_plots = []
    for k in sorted(categories):
        cat_data = [(lk,lv) for lk,lv in sorted(categories[k].items(), key=lambda kv: kv[1]) if lv>1]
        cat_data = cat_data[-10:]
        if len(cat_data) >= 2:
            p = create_category_hbar(k, cat_data)
            cat_plots.append(p)

    p = create_date_plot(x, y)
    r = row(p, column(*cat_plots))
    script,div = plot_html(r)
    return script + div


def create_date_plot(x, y):
    p = figure(title='Published pubtator COVID-19 articles', x_axis_type='datetime', sizing_mode='stretch_both', tools='pan,box_zoom,reset')
    zoom = WheelZoomTool(dimensions='width')
    p.add_tools(zoom)
    p.toolbar.active_scroll = zoom
    p.xaxis.axis_label = 'Time'
    p.yaxis.axis_label = 'Articles'
    dtf = DatetimeTickFormatter()
    dtf.milliseconds = ['%T']
    dtf.seconds = dtf.minsec = ['%T']
    dtf.hours = dtf.hourmin = dtf.minutes = ['%R']
    dtf.days = ['%b %e']
    dtf.months = ['%F']
    dtf.years = ['%F']
    p.xaxis.formatter = dtf
    p.vbar(x=x, top=y, width=24*60*60*1000)
    return p


def create_category_hbar(category, data):
    '''Data in the format [('Label 1',52), ('Label 2, 148'), ...] in ascending order.'''
    labels = [k for k,v in data]
    p = figure(title=category, y_range=labels, sizing_mode='stretch_both', tools=['tap'], plot_height=180)
    ds = ColumnDataSource(dict(labels=labels, value=[v for k,v in data]))
    p.hbar(y='labels', right='value', height=0.9, source=ds)
    ds.selected.js_on_change(
            'indices',
            CustomJS(args=dict(labels=labels),
                    code='''var label = labels[cb_obj.indices[0]];
                            var url = new URL(window.location.href);
                            var category = "%s";
                            var lst = url.searchParams.get(category) || [];
                            if (typeof lst.push !== "function") {
                                lst = [lst];
                            }
                            lst.push(label);
                            url.searchParams.set(category, lst);
                            window.location.assign(url);''' % category))
    return p


app.run(host='0.0.0.0', port=8080)
