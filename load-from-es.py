#!/usr/bin/env python3

from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

for r in es.search(index='pubtator-covid-19', size=100)['hits']['hits']:
    s = r['_source']
    print(s)
    # if 'title' in s:
        # print(s['title'])
