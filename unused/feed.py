#!/usr/bin/env python3

from pprint import pprint
import requests


api_key = ''
api_secret = ''
bearer_token = ''


search = 'ai (medicine OR healthcare)'
fields = 'tweet.fields=geo,created_at'
start_time = '2020-10-12T12:00:00Z'
end_time   = '2020-10-12T13:00:01Z'
limit = 100
url = 'https://api.twitter.com/2/tweets/search/recent?%s&start_time=%s&end_time=%s&max_results=%s&query=%s' % (fields, start_time, end_time, limit, search)
r = requests.get(url, headers={'Authorization': 'Bearer '+bearer_token}).json()
for tweet in r['data']:
    pprint(tweet)
