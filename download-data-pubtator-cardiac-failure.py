#!/usr/bin/env python3

import json
import requests

term = 'cardiac failure'
term = term.replace(' ', '+')
articles = []
idx = 0
while idx < 1000:
    url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retstart=%i&retmax=1000&term=%s' % (idx, term)
    print(url, end='\r')
    info = requests.get(url).json()
    article_ids = info['esearchresult']['idlist']
    articles += article_ids
    idx += len(article_ids)
    if len(article_ids) < 990:
        break
print()

article_term = ','.join(articles[-100:])
url = 'https://www.ncbi.nlm.nih.gov/research/pubtator-api/publications/export/biocjson?pmids=%s' % article_term
print(url)
info = requests.get(url)
for line in info.text.splitlines():
    print(json.loads(line))
