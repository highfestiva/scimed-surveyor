#!/usr/bin/env python3

from collections import defaultdict
from elasticsearch import Elasticsearch
from json import loads
import re

journal_split_regexp = re.compile(r'[\.;,]')
date_match = re.compile(r'(19\d\d|20\d\d)')
date_end_fix = re.compile(r'[A-Za-z]{3}[-/]([A-Za-z]{3})')
date_pick = re.compile(r'(\d{4}) .*?([A-Z][a-z]{2}|\d\d)\s*(\d{1,2}|)\b.*')
date_replacements = {   ' / ': '/',
                        ' - ': '-',
                        'Spring': 'May',
                        'Summer': 'Aug',
                        'Autumn': 'Nov',
                        'Fall':   'Nov',
                        'Winter': 'Feb'     }
mon_replacements = {mon.title():str(i+1) for i,mon in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split())}


def datefmt(unit, maxval):
    if unit and unit.isdecimal():
        ui = int(unit)
        if 1 <= ui <= maxval:
            return '-%.2i'%int(ui)
    return ''


articles = []
for line in open('litcovid2pubtator.json'):
    if '"_id": ' in line[:15]:
        # print('---------------------')
        line = loads(line[1:])
        pubmed_id = line['_id'].split('|')[0]
        title = ''
        date = orig_date = None
        annotations = defaultdict(set)
        for passage in line['passages']:
            if not title and passage['infons']['type'] in ('front','title'):
                title = passage['text']
                if 'journal' in passage['infons']:
                    journal = passage['infons']['journal']
                    orig_date = journal
                    dates = [s.strip() for s in journal_split_regexp.split(journal)]
                    dates = [s for s in dates if date_match.match(s)]
                    if dates:
                        date = dates[0]
                        for k,v in date_replacements.items():
                            date = date.replace(k,v)
                        date = date_end_fix.sub(r'\1', date)
                        ymd = date_pick.sub(r'\1 \2 \3', date).split()
                        ymd += [''] * (3-len(ymd))
                        year,month,day = ymd
                        for k,v in mon_replacements.items():
                            month = month.replace(k,v)
                        date = year + datefmt(month, 12) + datefmt(day, 31)
                        # print(date, orig_date, title)
            if 'annotations' in passage:
                for a in passage['annotations']:
                    annotations[a['infons']['type'].lower()].add(a['text'].lower())
        annotations = {k:sorted(v) for k,v in annotations.items()}
        article = {'id':pubmed_id, 'date':date, 'title':title, 'annotations':annotations}
        articles.append(article)
        if len(articles) == 5000:
            break

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def save(article):
    # print(article)
    res = es.index(index='pubtator-covid-19', body=article)
    # print(res['_id'])

for article in articles:
    print(article['date'], '~', article['title'])
    save(article)

print('looked through %i articles' % len(articles))
