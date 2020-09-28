#!/usr/bin/env python3

import requests


api_key = 'rY81K2dUBkhqZU5BVWFEDtSKq'
api_secret = 'B3gK5ndNu4NHcjsgl9sTIZPy7xMWo8TfkNsEIdALY3LYCGzyUk'
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAIoNHwEAAAAAGkPYnxky2SF6Hw0bjgGPefcDB6A%3DDHMd9NjSMYuGtbtRVD3o8XJJcsf32v9ZBsUSSCEVFjVu0qO3LQ'


search = '%23COVID'
r = requests.get('https://api.twitter.com/2/tweets/search/recent?query='+search, headers={'Authorization': 'Bearer '+bearer_token}).json()
for tweet in r['data']:
    print(tweet['text'])
