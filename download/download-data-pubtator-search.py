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
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retstart=%i&retmax=1000&term=%s' % (idx, term)
    print(url, end='\r')
    info = requests.get(url).json()
    article_ids = info['esearchresult']['idlist']
    articles += article_ids
    idx += len(article_ids)
    if len(article_ids) < 990:
        break
print()

w = open('data/%s.json' % term, 'w')
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
print('saved articles:', saved_cnt)
