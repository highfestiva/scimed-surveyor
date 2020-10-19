#!/usr/bin/env python3

import argparse
import json
import requests


parser = argparse.ArgumentParser()
parser.add_argument('search', nargs='+', help='search term, e.g. "cardiac failure"')
parser.add_argument('--limit', default=1000, type=int, help='number or articles to fetch from pubmed')
options = parser.parse_args()


term = ' '.join(options.search).replace(' ', '+')
articles = []
idx = 0
while idx < options.limit:
    limit = 1000 if options.limit>=1000 else options.limit
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retstart=%i&retmax=%s&term=%s' % (idx, limit, term)
    print(url[:130], end='\r')
    info = requests.get(url).json()
    article_ids = info['esearchresult']['idlist']
    articles += article_ids
    idx += len(article_ids)
    if len(article_ids) < 990:
        break
print()

name = term.replace('"','')
name = '-'.join(name.split('+')[:5])
w = open('data/%s.json' % name, 'w')
chunk_cnt = 90
saved_cnt = 0
for i in range(0, len(articles), chunk_cnt):
    article_term = ','.join(articles[i:i+chunk_cnt])
    url = 'https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson?pmids=%s' % article_term
    print('\r'+article_term[:60]+'... ', end='')
    r = requests.get(url)
    assert r.status_code == 200
    for line in r.text.splitlines():
        print(','+line, file=w) # prefix with comma for ES loader
        saved_cnt += 1
print()
print('saved pubtator articles:', saved_cnt)
