#!/usr/bin/env python3

import argparse
from elasticsearch import Elasticsearch
import json


def clean_hashtag(tag):
    tag = tag.lower()
    if not tag[-1].isalnum():
        tag = tag[:-1]
    return tag


def read_tweet(text, options):
    tweet = json.loads(text)
    text = tweet['text'].strip('…')
    tweet['date'] = tweet['created_at'].partition(':')[0] + 'Z'
    tweet['annotations'] = {'hashtag': [clean_hashtag(w) for w in text.split() if w[0]=='#']}
    return tweet



parser = argparse.ArgumentParser()
parser.add_argument('--reset-index', action='store_true', default=False, help='delete index before inserting anything new')
parser.add_argument('--index', required=True, help='index to insert into, e.g. "twitter-health-19"')
options = parser.parse_args()


es = Elasticsearch([{'host': 'localhost', 'port': 9200}], http_auth=('elastic', open('../http-server/.espassword').read().strip()))
if options.reset_index:
    print('deleting index', options.index)
    es.indices.delete(index=options.index, ignore=[400, 404])

print('saving...')
saved_cnt = lines = 0
for line in open('data/twitter.json'):
    tweet = read_tweet(line, options)
    if tweet:
        if saved_cnt%11 == 0:
            print('\r%s' % tweet['date'], end=' ')
        res = es.index(index=options.index, body=tweet)
        saved_cnt += 1
    lines += 1

print()
print('saved %i/%i tweets' % (saved_cnt, lines))
