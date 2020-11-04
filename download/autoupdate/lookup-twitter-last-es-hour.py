#!/usr/bin/env python3

from elasticsearch import Elasticsearch
from os import getenv


def lookup(index, user='elastic', password=None):
    eshost = getenv('ESHOST', 'localhost')
    es = Elasticsearch([{'host': eshost, 'port': 9200}], http_auth=(user, password))
    r = es.search(index=index, size=1, sort='created_at:desc')
    for doc in r['hits']['hits']:
        last = doc['_source']['date']
        print(last)
        return last


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', required=True, help='index to search for last entry, e.g. "twitter-tech"')
    options = parser.parse_args()
    password = open('.espassword').read().strip()
    lookup(index=options.index, password=password)
