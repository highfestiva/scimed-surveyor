#!/usr/bin/env python3

import bokeh
from bokeh.embed import json_item
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.models.formatters import DatetimeTickFormatter, FuncTickFormatter
from bokeh.plotting import figure
import calendar
from collections import defaultdict
from conf.settings import page_settings
from copy import deepcopy
from elasticsearch import Elasticsearch
from flask import Flask, jsonify, request, render_template, send_from_directory
from frozendict import frozendict
from functools import lru_cache
import json
import journal_util
from journal_countrycode import journal2country_code, doi2cc
from os import getenv
import pandas as pd
import urllib.parse
from world_country_score import plot_map


chunk_hits = 10000
eshost = getenv('ESHOST', 'localhost')
version = getenv('SCIMEDVER', 'v0.1')
es = Elasticsearch([{'host': eshost, 'port': 9200}], http_auth=('elastic', open('.espassword').read().strip()))
app = Flask(__name__)
minutes_ms = 60*1000
hours_ms = 60*minutes_ms
days_ms = 24*hours_ms

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


@app.route('/')
def index():
    indices = sorted(i for i,v in es.indices.get_alias('*').items() if '.' not in i and not v['aliases'])
    dsources = defaultdict(list)
    for i in indices:
        dsource,area = i.split('-',1)
        name = area
        url = dsource + '/' + area
        f = get_setting(i+'.filter')
        if f:
            print(f, type(f), json.dumps(f))
            url += '?filter=' + urllib.parse.quote(json.dumps(f).replace(' ',''))
        dsources[dsource] += [{'name':name, 'url':url}]
    return render_template('landing.html', dsources=dsources)


@app.route('/<dsource>/<area>')
def page_main(dsource, area):
    return render_template('research.html', bokeh_version=bokeh.__version__, dsource=dsource, area=area, ssver=version)


@app.route('/<dsource>/<area>/plot-main')
def plot_main(dsource, area):
    index = '%s-%s' % (dsource, area)
    l_args = get_l_args()
    time_zone_offset = int(request.values.get('tz', '0')) * minutes_ms
    sample_t = get_setting(index+'.period', days_ms)
    docs = fetch_docs(index=index, annotations=l_args[0])
    main_plot = create_main_plot(docs, dsource, area, l_args, time_zone_offset=time_zone_offset, sample_t=sample_t)
    for i,sargs in enumerate(l_args[1:]):
        docs2 = fetch_docs(index=index, annotations=sargs)
        df = docs2df(docs2, time_zone_offset, sample_t)
        add_line(main_plot['plot'], df, color=i+1, legend=args2str(dsource, area, sargs))
    main_plot['plot'] = json_item(main_plot['plot'])
    plots = create_annotation_plots(index, docs, limit=7)
    articles = tweetify(docs) if dsource == 'twitter' else articlify(docs)
    annotation_suffix = len(plots)
    nouns = nounify(dsource)
    has_map = get_setting(index+'.map', True)
    return jsonify({'main':main_plot, 'annotations':plots, 'annot-suffix':annotation_suffix, 'article-header':'Latest '+nouns+main_plot['filter-suffix'], 'articles':articles[:50], 'has-map':has_map})


@app.route('/<dsource>/<area>/plot-world-map')
def plot_world_map(dsource, area):
    try:
        index = '%s-%s' % (dsource, area)
        l_args = get_l_args()
        docs = fetch_docs(index=index, annotations=l_args[0])
        cc2score = defaultdict(int)
        for doc in docs:
            journal,doip = journal_util.extract(doc['journal'])
            cc = journal2country_code.get(journal)
            if not cc:
                cc = doi2cc.get(doip)
            if cc:
                cc2score[cc] += 1
        p = plot_map(cc2score)
        nouns = nounify(dsource)
        map_title = '%i %s %s in %i countries' % (len(docs), area, nouns, len(cc2score))
        return {'name':map_title, 'plot': json_item(p)}
    except:
        return {}, 400


@app.route('/<dsource>/<area>/list-labels/<annotation>')
def list_labels(dsource, area, annotation):
    index = '%s-%s' % (dsource, area)
    l_args = get_l_args()
    docs = fetch_docs(index=index, annotations=l_args[0])
    annotations = sum_annotations(index, docs, only_annotation=annotation)
    for k,v in annotations.items():
        annotations[k] = sorted(v.items(), key=lambda kv:-kv[1])
    r = {'annotations':[{'name':k, 'labels':v} for k,v in annotations.items()]}
    for a in r['annotations']:
        aname = a['name']
        if l_args[0]:
            items = sorted(l_args[0].items(), key=lambda kv: -1 if kv[0]==aname else 1)
            sargs = ' AND '.join([(('%s=%s'%(k,v)) if k!=aname else v) for k,v in items])
            aname += ' (FILTERED BY %s)' % sargs
        a['fullname'] = aname
    return jsonify(r)


@app.route('/<dsource>/<area>/compare-annotations')
def compare_annotations(dsource, area):
    index = '%s-%s' % (dsource, area)
    filters = []
    for args in get_l_args():
        items = sorted(args.items())
        sargs = ' AND '.join([('%s=%s'%(k,v)) for k,v in items])
        docs = fetch_docs(index=index, annotations=args)
        plots = create_annotation_plots(docs, limit=10, skip_empty=False)
        filters.append({'title': sargs, 'annotations': json.dumps(plots)})
    return render_template('compare-annotations.html', bokeh_version=bokeh.__version__, dsource=dsource, area=area, ssver=version, filters=filters)


def get_l_args():
    v = eval(request.args.get('filter', '{}'))
    if type(v) != list:
        v = [v]
    for vv in v:
        for k,w in vv.items():
            vv[k] = ','.join(w)
    return v


def fetch_docs(index, annotations=None):
    return deepcopy(_fetch_docs(index, frozendict(annotations)))


@lru_cache(maxsize=4)
def _fetch_docs(index, annotations):
    kwargs = {}
    if annotations:
        kwargs = {'body': deepcopy(es_query)}
        kwargs['body']['query']['bool']['must'] = [{'match': {'annotations.'+k:vv.strip('#').replace(' ','_')}} for k,v in annotations.items() for vv in v.split(',')]
        print(kwargs)
    docs = []
    r = es.search(index=index, size=chunk_hits, scroll='2s', **kwargs)
    while len(r['hits']['hits']):
        docs.extend(r['hits']['hits'])
        r = es.scroll(scroll_id = r['_scroll_id'], scroll = '2s')
    docs = [d['_source'] for d in docs]
    docs = [d for d in docs if d['date']] # only keep documents with dates
    print('%s docs found.' % len(docs))
    return docs


def sum_annotations(index, docs, only_annotation):
    skip_annotations = set(get_setting(index+'.exclude-annotations', default=[]))
    annotations = defaultdict(lambda: defaultdict(int))
    for doc in docs:
        for k,v in doc['annotations'].items():
            if k in skip_annotations:
                continue
            if only_annotation and k != only_annotation:
                continue
            for label in v:
                label = label.replace('_', ' ')
                annotations[k][label] += 1
    return annotations


def create_main_plot(docs, dsource, area, l_args, time_zone_offset, sample_t):
    df = docs2df(docs, time_zone_offset, sample_t)

    # create main plot
    nouns = nounify(dsource)
    dsourcename = '' if nouns=='tweets' else dsource
    main_title = '%i %s %s %s' % (len(docs), area, dsourcename, nouns)
    filter_suffix = ''
    sargs = args2str(dsource, area, l_args[0])
    if l_args[0]:
        filter_suffix = ' (FILTERED BY %s)' % sargs
        main_title += filter_suffix
    p = create_date_plot(dsource, df, sample_t, legend=sargs if len(l_args)>=2 else None)
    return {'name':main_title, 'filter-suffix':filter_suffix, 'plot':p}


def create_annotation_plots(index, docs, limit, skip_empty=True):
    annotations = sum_annotations(index, docs, only_annotation=None)

    plots = []
    for k in sorted(annotations):
        data = [(lk,lv) for lk,lv in sorted(annotations[k].items(), key=lambda kv: kv[1]) if lv>1]
        data = data[-limit:]
        if not skip_empty or len(data) >= 2:
            if len(data) >= 2 or (not skip_empty and len(data)==1):
                p = json_item(create_annotation_hbar(k, data, col_index=len(plots)))
            else:
                p = ''
            plots.append({'name':k, 'plot':p})
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


def tweetify(docs):
    tweets = []
    for doc in docs:
        tweets.append({'title':doc['text'], 'date':doc['created_at'].replace('T', ' '), 'url':'https://twitter.com/i/web/status/%s'%doc['id']})
    return sorted(tweets, key=lambda a: a['date'], reverse=True)


def articlify(docs):
    articles = []
    for doc in docs:
        articles.append({'title':doc['title'], 'date':doc['date'], 'url':'https://www.ncbi.nlm.nih.gov/research/pubtator/?pmid=%s'%doc['id']})
    return sorted(articles, key=lambda a: a['date'], reverse=True)


def nounify(dsource):
    return 'tweets' if dsource=='twitter' else 'articles'


def _get_setting(key_parts):
    d = page_settings
    v = None
    for k in key_parts:
        if k in d:
            v = d = d[k]
        else:
            return None
    return v


def get_setting(key, default=None):
    key_parts = key.split('.')
    val = _get_setting(key_parts)
    if val is None:
        val = _get_setting(['<default>']+key_parts[1:])
    if val is None:
        val = default
    return val


def args2str(dsource, area, args):
    if not args:
        return '%s %s (unfiltered)' % (dsource, area)
    return ' AND '.join([('%s=%s'%(k,v)) for k,v in args.items()])


def docs2df(docs, time_zone_offset, sample_t):
    data = defaultdict(int)
    for doc in docs:
        data[doc['date']] += 1
    smear_partial_dates(data)
    df = pd.DataFrame(sorted((k,v) for k,v in data.items()), columns=['t','n'])
    tzoff = 0 if sample_t >= days_ms else time_zone_offset # only offset by timezone in intra-daily resolution
    df['t'] = pd.to_datetime(df.t) + pd.Timedelta(tzoff + sample_t//2, unit='ms') # adjust by timezone, and shift right of X-axis labels
    return df


def create_date_plot(dsource, df, sample_t, legend):
    x0,x1 = x_rng_percentile(dsource, df, 1)
    ymax = df.n.max() * 1.05
    p = figure(x_range=(x0, x1), y_range=(0,ymax), x_axis_type='datetime', sizing_mode='stretch_both', tools='pan,box_zoom,xwheel_zoom,reset', active_scroll='xwheel_zoom')
    p.toolbar.logo = None
    dtf = DatetimeTickFormatter()
    dtf.milliseconds = ['%T']
    dtf.seconds = dtf.minsec = ['%T']
    dtf.hours = dtf.hourmin = dtf.minutes = ['%R']
    dtf.days = ['%b %e']
    dtf.months = ['%F']
    dtf.years = ['%F']
    p.xaxis.formatter = dtf
    p.xgrid.grid_line_color = None
    p.vbar(x=df.t, top=df.n, width=sample_t, color='#ccffcc')
    add_line(p, df, color=0, legend=legend)
    return p


def add_line(p, df, color, legend=None):
    if len(df) > 50:
        smooth = df.n.rolling(14, center=True).mean()
        kw = {'legend_label':legend} if legend else {}
        colors = ['#005500', '#ccaa00', '#1166cc', '#ee22ff', '#44ddbb']
        color = colors[color%len(colors)]
        p.line(x=df.t, y=smooth, color=color, **kw)


def x_rng_percentile(dsource, df, pct):
    # twitter assumed to have linear time distribution (while articles don't)
    if dsource=='twitter' or len(df) < 20:
        return df['t'].iloc[0], df['t'].iloc[-1]
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
    colors = [('#87cded', '#a7edfd'), ('#c0c610', '#d0ff14'), ('#ff7034', '#ff9044'), ('#ff9889', '#ffb8a9'), ('#f4bfff', '#f8dfff'), ('#bff4bb', '#dff8dd'), ('#c0c0c0', '#b0b0b0'), ('#ff80a0', '#ff90b0')]
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
                            var filter = JSON.parse(url.searchParams.get("filter")) || [{}];
                            filter[0]["%s"] = (filter[0]["%s"] || []).concat(label);
                            url.searchParams.set("filter", JSON.stringify(filter));
                            window.location.assign(url);''' % (annotation, annotation)))
    return p


# wait for Elasticsearch
for _ in range(30):
    if es.ping():
        break
    import time
    time.sleep(1)
assert es.ping()


app.run(host='0.0.0.0', port=8080)
