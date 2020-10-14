#!/usr/bin/env python3

import bokeh
from bokeh.embed import json_item
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, WheelZoomTool
from bokeh.models.formatters import DatetimeTickFormatter, FuncTickFormatter
from bokeh.palettes import cividis, Category20
from bokeh.plotting import figure
import calendar
from collections import defaultdict
from copy import deepcopy
from dateutil import parser as date_parser
from flask import Flask, jsonify, request, render_template, send_from_directory
from elasticsearch import Elasticsearch
from os import getenv
import pandas as pd


chunk_hits = 10000
eshost = getenv('ESHOST', 'localhost')
version = getenv('SCIMEDVER', 'v0.1')
es = Elasticsearch([{'host': eshost, 'port': 9200}])
app = Flask(__name__)

es_query = {
    'query': {
        'bool': {
            'must': []
        }
    }
}

skip_annotations = ('species',)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'vgr.ico', mimetype='image/x-icon')


@app.route('/<dsource>/<area>')
def page_main(dsource, area):
    return render_template('research.html', bokeh_version=bokeh.__version__, dsource=dsource, area=area, ssver=version)


@app.route('/<dsource>/<area>/plot-main')
def plot_main(dsource, area):
    index = '%s-%s' % (dsource, area)
    docs = fetch_docs(index=index, annotations=request.args)
    main_plot = create_main_plot(docs, dsource, area)
    plots = create_annotation_plots(docs, limit=7) if dsource=='pubtator' else []
    articles = articlify(docs) if dsource=='pubtator' else []
    return jsonify({'main':main_plot, 'annotations':plots, 'article-header':'Latest articles'+main_plot['filter-suffix'], 'articles':articles[:50]})


@app.route('/<dsource>/<area>/list-labels/<annotation>')
def list_labels(dsource, area, annotation):
    index = '%s-%s' % (dsource, area)
    docs = fetch_docs(index=index, annotations=request.args)
    annotations = sum_annotations(docs, only_annotation=annotation)
    for k,v in annotations.items():
        annotations[k] = sorted(v.items(), key=lambda kv:-kv[1])
    r = {'annotations':[{'name':k, 'labels':v} for k,v in annotations.items()]}
    for a in r['annotations']:
        aname = a['name']
        if request.args:
            items = sorted(request.args.items(), key=lambda kv: -1 if kv[0]==aname else 1)
            sargs = ' AND '.join([(('%s=%s'%(k,v)) if k!=aname else v) for k,v in items])
            aname += ' (FILTERED BY %s)' % sargs
        a['fullname'] = aname
    return jsonify(r)


def fetch_docs(index, annotations=None):
    kwargs = {}
    if annotations:
        kwargs = {'body': deepcopy(es_query)}
        kwargs['body']['query']['bool']['must'] = [{'match': {'annotations.'+k:vv}} for k,v in annotations.items() for vv in v.split(',')]
        print(kwargs)
    docs = []
    r = es.search(index=index, size=chunk_hits, scroll='2s', **kwargs)
    while len(r['hits']['hits']):
        docs.extend(r['hits']['hits'])
        r = es.scroll(scroll_id = r['_scroll_id'], scroll = '2s')
    docs = [d['_source'] for d in docs]
    docs = [d for d in docs if d['date']] # only keep documents with dates
    return docs


def sum_annotations(docs, only_annotation):
    annotations = defaultdict(lambda: defaultdict(int))
    for doc in docs:
        for k,v in doc['annotations'].items():
            if k in skip_annotations:
                continue
            if only_annotation and k != only_annotation:
                continue
            for label in v:
                annotations[k][label] += 1
    return annotations


def create_main_plot(docs, dsource, area):
    data = defaultdict(int)
    for doc in docs:
        data[doc['date']] += 1
    smear_partial_dates(data)
    df = pd.DataFrame(sorted((k,v) for k,v in data.items()), columns=['t','n'])
    df['t'] = pd.to_datetime(df.t)

    # create main plot
    main_title = '%i %s %s articles' % (len(docs), area, dsource)
    filter_suffix = ''
    if request.args:
        sargs = ' AND '.join([('%s=%s'%(k,v)) for k,v in request.args.items()])
        filter_suffix = ' (FILTERED BY %s)' % sargs
        main_title += filter_suffix
    p = create_date_plot(df)
    return {'name':main_title, 'filter-suffix':filter_suffix, 'plot':json_item(p)}


def create_annotation_plots(docs, limit):
    annotations = sum_annotations(docs, only_annotation=None)

    plots = []
    for k in sorted(annotations):
        data = [(lk,lv) for lk,lv in sorted(annotations[k].items(), key=lambda kv: kv[1]) if lv>1]
        data = data[-limit:]
        if len(data) >= 2:
            p = create_annotation_hbar(k, data, col_index=len(plots))
            plots.append({'name':k, 'plot':json_item(p)})
    return plots


def smear_partial_dates(data):
    '''2020-04 -> every day of month. Same applies to year.'''
    for date,cnt in list(data.items()):
        months = []
        outp_dates = []
        if len(date) <= 4:
            year = int(date)
            months = range(1, 12+1)
        elif len(date) <= 7:
            year,month = [int(e) for e in date.split('-')]
            months = [month]
        for month in months:
            num_days = calendar.monthrange(year, month)[1]
            outp_dates += ['%i-%.2i-%.2i' % (year, month, day) for day in range(1, num_days+1)]
        if outp_dates:
            val = cnt / len(outp_dates)
            for d in outp_dates:
                data[d] += val
            del data[date]


def articlify(docs):
    articles = []
    for doc in docs:
        articles.append({'title':doc['title'], 'date':doc['date'], 'url':'https://www.ncbi.nlm.nih.gov/research/pubtator/?pmid=%s'%doc['id']})
    return sorted(articles, key=lambda a: a['date'], reverse=True)


def create_date_plot(df):
    x0,x1 = x_rng_percentile(df, 1)
    ymax = df.n.max() * 1.05
    p = figure(x_range=(x0, x1), y_range=(0,ymax), x_axis_type='datetime', sizing_mode='stretch_both', tools='pan,box_zoom,reset')
    p.toolbar.logo = None
    zoom = WheelZoomTool(dimensions='width')
    p.add_tools(zoom)
    p.toolbar.active_scroll = zoom
    dtf = DatetimeTickFormatter()
    dtf.milliseconds = ['%T']
    dtf.seconds = dtf.minsec = ['%T']
    dtf.hours = dtf.hourmin = dtf.minutes = ['%R']
    dtf.days = ['%b %e']
    dtf.months = ['%F']
    dtf.years = ['%F']
    p.xaxis.formatter = dtf
    p.xgrid.grid_line_color = None
    p.vbar(x=df.t, top=df.n, width=24*60*60*1000, color='#ccffcc')
    smooth = df.n.rolling(14, center=True).mean()
    p.line(x=df.t, y=smooth, color='#005500')
    return p


def x_rng_percentile(df, pct):
    '''Drop first and last n percentiles. Return x0, x1.'''
    s = df.n.sum()
    cs = df.n.fillna(0).cumsum()
    x0 = df.loc[cs > s*pct/100, 't'].iloc[0]
    x1 = df.loc[cs < s*(100-pct)/100, 't'].iloc[-1]
    return x0, x1


def create_annotation_hbar(annotation, data, col_index=0):
    '''Data in the format [('Label 1',52), ('Label 2, 148'), ...] in ascending order.'''
    labels = [k for k,v in data]
    values = [v for k,v in data]
    xmax = max(values) * 1.05
    p = figure(x_range=(0, xmax), y_range=labels, sizing_mode='stretch_both', toolbar_location=None, tools=['tap'], plot_height=180)
    p.xaxis.formatter = FuncTickFormatter(code='return tick? tick : "";')
    p.yaxis.visible = False
    p.min_border_left = 0
    p.min_border_right = 0
    p.min_border_top = 0
    p.min_border_bottom = 0
    p.ygrid.grid_line_color = None
    colors = [('#87cded', '#a7edfd'), ('#c0c610', '#d0ff14'), ('#ff7034', '#ff9044'), ('#ff9889', '#ffb8a9'), ('#f4bfff', '#f8dfff')]
    cmap = colors[col_index%len(colors)] * int(len(labels)/2+1)
    cmap = cmap[:len(labels)][::-1]
    ds = ColumnDataSource(dict(labels=labels, value=values, color=cmap))
    p.hbar(y='labels', right='value', height=0.9, color='color', source=ds)
    p.text(y='labels', text='labels', text_baseline='middle', x=0, x_offset=3, text_font_size='9px', source=ds)
    ds.selected.js_on_change(
            'indices',
            CustomJS(args=dict(labels=labels),
                    code='''var label = labels[cb_obj.indices[0]];
                            var url = new URL(window.location.href);
                            var annotation = "%s";
                            var lst = url.searchParams.get(annotation) || [];
                            if (typeof lst.push !== "function") {
                                lst = [lst];
                            }
                            lst.push(label);
                            url.searchParams.set(annotation, lst);
                            window.location.assign(url);''' % annotation))
    return p


# wait for Elasticsearch
for _ in range(30):
    if es.ping():
        break
    import time
    time.sleep(1)
assert es.ping()


app.run(host='0.0.0.0', port=8080)
