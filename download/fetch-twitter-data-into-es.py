#!/usr/bin/env python3

import argparse
import dateutil.parser
from datetime import datetime
from elasticsearch import Elasticsearch
import importlib.util
import requests
import pytz


spec = importlib.util.spec_from_file_location('twitterkey', '.twitterkey.py')
twitterkey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twitterkey)


def utc2timestamp(s):
    return int(dateutil.parser.parse(s).replace(tzinfo=pytz.utc).timestamp())


def timestamp2utc(t):
    return datetime.utcfromtimestamp(t).isoformat() + 'Z'


def search(start_time, end_time, options):
    fields = 'tweet.fields=geo,created_at'
    url = 'https://api.twitter.com/2/tweets/search/recent?%s&start_time=%s&end_time=%s&max_results=%s&query=%s' % (fields, start_time, end_time, options.interval_limit, options.search)
    r = requests.get(url, headers={'Authorization': 'Bearer '+twitterkey.bearer_token}).json()
    for tweet in r['data']:
        tweet['date'] = tweet['created_at']
        del tweet['created_at']
        yield tweet



parser = argparse.ArgumentParser()
parser.add_argument('--reset-index', action='store_true', default=False, help='delete index before inserting anything new')
parser.add_argument('--index', required=True, help='index to insert into, e.g. "twitter-health-19"')
parser.add_argument('--start-time', required=True, help='e.g. 2020-10-14T12:00:00Z')
parser.add_argument('--end-time', required=True, help='e.g. 2020-10-14T13:00:00Z')
parser.add_argument('--stride-time', default='1:00', help='sample period in seconds, default 1:00')
parser.add_argument('--search', required=True, help='e.g. "ai (medicine OR healthcare)"')
parser.add_argument('--interval-limit', default=100, type=int, help='how many tweets to download per minute')
options = parser.parse_args()


es = Elasticsearch([{'host': 'localhost', 'port': 9200}])
if options.reset_index:
    print('deleting index', options.index)
    es.indices.delete(index=options.index, ignore=[400, 404])


print('saving...')
st = utc2timestamp(options.start_time)
et = utc2timestamp(options.end_time)
step = sum([int(v)*60**i for i,v in enumerate(reversed(options.stride_time.split(':')))])
saved_cnt = 0
for t in range(st, et+step, step):
    start_time = timestamp2utc(t)
    end_time = timestamp2utc(t+step+1)
    print('\r'+start_time, end='')
    for tweet in search(start_time, end_time, options):
        res = es.index(index=options.index, body=tweet)
        print(res)
        saved_cnt += 1

print()
print('saved %i tweets' % saved_cnt)
