#!/usr/bin/env python3

import argparse
from collections import defaultdict
from elasticsearch import Elasticsearch
from extra_annotations import extra_annotations
from json import loads
import re


parser = argparse.ArgumentParser()
parser.add_argument('--index', required=True, help='index to insert into, e.g. "pubtator-covid-19"')
parser.add_argument('--limit', default=100_000, type=int, help='number or articles to insert into Elasticsearch')
parser.add_argument('file', help='JSON file containing pubtator data')
options = parser.parse_args()


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


print('loading mesh files...')
id2shortname = {}
for fname,term_id in [('c2020.bin', 'NM ='), ('d2020.bin','MH ='), ('q2020.bin','SH = ')]:
    for line in open('data/'+fname, encoding='utf8'):
        if line.startswith(term_id):
            term = line.partition(' = ')[2].strip()
        elif line.startswith('UI ='):
            mid = 'MESH:' + line.partition(' = ')[2].strip()
            assert mid and mid not in id2shortname
            id2shortname[mid] = term


# create a gene dict based on prevalence
gene2word2cnt = defaultdict(lambda: defaultdict(int))
print('checking gene prevalence...')
for i,line in enumerate(open(options.file)):
    if '"_id": ' in line[:15]:
        if i%23 == 0:
            print('%i'%i, end='\r')
        line = loads(line[1:])
        for passage in line['passages']:
            pas = passage.get('annotations') or []
            for a in pas:
                infons = a['infons']
                if infons['type'] == 'Gene':
                    gid = infons['identifier']
                    if not gid:
                        gid = a['text']
                    gene2word2cnt[gid][a['text']] += 1
for gid,word2cnt in gene2word2cnt.items():
    most_common = sorted(word2cnt.items(), key=lambda kv:-kv[1])[0][0]
    assert gid and gid not in id2shortname
    id2shortname[gid] = most_common


print('loading data...')
articles = []
for line in open(options.file):
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
            # add annotations
            pas = passage.get('annotations') or []
            for a in pas:
                infons = a['infons']
                lookup = infons.get('identifier')
                txt = id2shortname.get(lookup)
                annotations[infons['type'].lower()].add(txt or a['text'].lower())
            # manual annotations
            text = passage.get('text')
            if text:
                text = text.lower()
                for topic,values in extra_annotations.items():
                    for value in values:
                        if value in text and re.search(r'\b%s\b'%value, text):
                            annotations[topic].add(value)
        annotations = {k:sorted(v) for k,v in annotations.items()}
        article = {'id':pubmed_id, 'date':date, 'title':title, 'annotations':annotations}
        articles.append(article)
        if len(articles) >= options.limit:
            break

def save(article):
    # print(article)
    res = es.index(index=options.index, body=article)
    # print(res['_id'])

print('deleting index', options.index)
es = Elasticsearch([{'host': 'localhost', 'port': 9200}], http_auth=('elastic', open('../http-server/.espassword').read().strip()))
es.indices.delete(index=options.index, ignore=[400, 404])

print('saving...')
for i,article in enumerate(articles):
    if i%23 == 0:
        print(i, article['date'], '~', article['title'][:50], end='\r')
    save(article)

print()
print('saved %i articles' % len(articles))
