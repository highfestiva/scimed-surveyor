#!/usr/bin/env python3

from elasticsearch import Elasticsearch
from json import loads

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

for r in es.search(index='covid-19-articles')['hits']['hits']:
    s = r['_source']
    if 'title' in s:
        print(s['title'])
