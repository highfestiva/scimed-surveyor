#!/usr/bin/env python3

import bokeh
from bokeh.embed import json_item
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, WheelZoomTool
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.palettes import Category20
from bokeh.plotting import figure
from collections import defaultdict
from copy import deepcopy
from dateutil import parser as date_parser
from flask import Flask, jsonify, request, render_template, send_from_directory
from elasticsearch import Elasticsearch


max_hits = 10000 # number of ES documents to return at most
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
app = Flask(__name__)

es_query = {
    'query': {
        'bool': {
            'must': []
        }
    }
}


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'vgr.ico', mimetype='image/x-icon')


@app.route('/covid-19')
def index():
    return render_template('covid-19-research.html', bokeh_version=bokeh.__version__)


@app.route('/plot/covid-19')
def plot(index='pubtator-covid-19'):
    kwargs = {}
    if request.args:
        kwargs = {'body': deepcopy(es_query)}
        kwargs['body']['query']['bool']['must'] = [{'match': {'annotations.'+k:vv}} for k,v in request.args.items() for vv in v.split(',')]
        print(kwargs)
    ss = es.search(index=index, size=max_hits, **kwargs)
    data = defaultdict(int)
    categories = defaultdict(lambda: defaultdict(int))
    articles = []
    for r in ss['hits']['hits']:
        s = r['_source']
        if not s['date']:
            continue
        articles.append({'title':s['title'], 'date':s['date'], 'url':'https://pubmed.ncbi.nlm.nih.gov/%s/'%s['id']})
        data[s['date']] += 1
        for k,v in s['annotations'].items():
            if k not in ('id','date','title'):
                for label in v:
                    categories[k][label] += 1

    series = sorted([(date_parser.isoparse(t),cnt) for t,cnt in data.items()])
    x = [t for t,cnt in series]
    y = [cnt for t,cnt in series]

    # create main plot
    main_title = '%i published pubtator COVID-19 articles' % len(articles)
    if request.args:
        sargs = ' AND '.join([('%s=%s'%(k,v)) for k,v in request.args.items()])
        main_title += ' (%s)' % sargs
    p = create_date_plot(main_title, x, y)
    main_plot = json_item(p)

    # create category plots
    cat_plots = []
    for k in sorted(categories):
        cat_data = [(lk,lv) for lk,lv in sorted(categories[k].items(), key=lambda kv: kv[1]) if lv>1]
        cat_data = cat_data[-10:]
        if len(cat_data) >= 2:
            p = create_category_hbar(k, cat_data)
            cat_plots.append({'name':k, 'plot':json_item(p)})

    # sort articles
    articles = sorted(articles, key=lambda a: a['date'], reverse=True)

    return jsonify({'main':main_plot, 'categories':cat_plots, 'articles':articles[:50]})


def create_date_plot(title, x, y):
    p = figure(title=title, x_axis_type='datetime', sizing_mode='stretch_both', tools='pan,box_zoom,reset')
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
    p.vbar(x=x, top=y, width=24*60*60*1000, color='#005500')
    return p


def create_category_hbar(category, data):
    '''Data in the format [('Label 1',52), ('Label 2, 148'), ...] in ascending order.'''
    labels = [k for k,v in data]
    p = figure(y_range=labels, sizing_mode='stretch_both', toolbar_location=None, tools=['tap'], plot_height=180)
    p.yaxis.visible = False
    p.min_border_left = 0
    p.min_border_right = 0
    p.min_border_top = 0
    p.min_border_bottom = 0
    ds = ColumnDataSource(dict(labels=labels, value=[v for k,v in data], color=Category20[max(3, len(labels))][::-1]))
    p.hbar(y='labels', right='value', height=0.9, color='color', source=ds)
    p.text(y='labels', text='labels', text_baseline='middle', x=0, x_offset=3, text_font_size='9px', source=ds)
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
