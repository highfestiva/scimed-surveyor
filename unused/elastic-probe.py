#!/usr/bin/env python3

from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
print(es.ping())
res = es.index(index='covid-19-articles', body={'something':'goes here'})
print(res)
