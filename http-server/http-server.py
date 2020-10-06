#!/usr/bin/env python3

import bokeh
from bokeh.embed import json_item
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, CustomJS, WheelZoomTool
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.palettes import cividis, Category20
from bokeh.plotting import figure
import calendar
from colorcet import glasbey
from collections import defaultdict
from copy import deepcopy
from dateutil import parser as date_parser
from flask import Flask, jsonify, request, render_template, send_from_directory
from elasticsearch import Elasticsearch


chunk_hits = 10000
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


@app.route('/<dsource>/<area>')
def page_main(dsource, area):
    return render_template('research.html', bokeh_version=bokeh.__version__, dsource=dsource, area=area)


@app.route('/<dsource>/<area>/annotation/<annotation>')
def page_annotation(dsource, area, annotation):
    return render_template('annotation.html', bokeh_version=bokeh.__version__, area=area, annotation=annotation)


@app.route('/<dsource>/<area>/plot-main')
def plot_main(dsource, area):
    index = '%s-%s' % (dsource, area)
    docs = fetch_docs(index=index, annotations=request.args)
    main_plot = create_main_plot(docs, dsource, area)
    plots = create_annotation_plots(docs, limit=8)
    articles = articlify(docs)
    return jsonify({'main':main_plot, 'annotations':plots, 'articles':articles[:50]})


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
    r['articles'] = articlify(docs)[:50]
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
    series = sorted([(date_parser.isoparse(t),cnt) for t,cnt in data.items()])
    x = [t for t,cnt in series]
    y = [cnt for t,cnt in series]

    # create main plot
    main_title = '%i published %s %s articles' % (len(docs), area, dsource)
    if request.args:
        sargs = ' AND '.join([('%s=%s'%(k,v)) for k,v in request.args.items()])
        main_title += ' (FILTERED BY %s)' % sargs
    p = create_date_plot(main_title, x, y)
    return json_item(p)


def create_annotation_plots(docs, limit):
    annotations = sum_annotations(docs, only_annotation=None)

    plots = []
    for k in sorted(annotations):
        data = [(lk,lv) for lk,lv in sorted(annotations[k].items(), key=lambda kv: kv[1]) if lv>1]
        data = data[-limit:]
        if len(data) >= 2:
            p = create_annotation_hbar(k, data)
            plots.append({'name':k, 'plot':json_item(p)})
    return plots


def smear_partial_dates(data):
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
        articles.append({'title':doc['title'], 'date':doc['date'], 'url':'https://pubmed.ncbi.nlm.nih.gov/%s/'%doc['id']})
    return sorted(articles, key=lambda a: a['date'], reverse=True)


def create_date_plot(title, x, y):
    x0,x1 = x_rng_percentile(1, x, y)
    p = figure(title=title, x_range=(x0, x1), x_axis_type='datetime', sizing_mode='stretch_both', tools='pan,box_zoom,reset')
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


def x_rng_percentile(n, x, y):
    '''Drop first and last n percentiles. Return x0, x1.'''
    p0 = sum(y)*n / 100
    p1 = sum(y)*(100-n) / 100
    x0 = x[0]
    x1 = x[-1]
    ys = 0
    for xx,yy in zip(x, y):
        if ys < p0:
            x0 = xx
        ys += yy
        if ys < p1:
            x1 = xx
    return x0, x1


def create_annotation_hbar(annotation, data):
    '''Data in the format [('Label 1',52), ('Label 2, 148'), ...] in ascending order.'''
    labels = [k for k,v in data]
    p = figure(y_range=labels, sizing_mode='stretch_both', toolbar_location=None, tools=['tap'], plot_height=180)
    p.yaxis.visible = False
    p.min_border_left = 0
    p.min_border_right = 0
    p.min_border_top = 0
    p.min_border_bottom = 0
    cmap = glasbey[:]#[8:] + glasbey[:8]
    if len(cmap) < len(labels):
        cmap = cmap * (len(labels)//len(cmap)+1)
    cmap = cmap[2:] + cmap[:2]
    cmap = cmap[:len(labels)][::-1]
    ds = ColumnDataSource(dict(labels=labels, value=[v for k,v in data], color=cmap))
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


app.run(host='0.0.0.0', port=8080)
