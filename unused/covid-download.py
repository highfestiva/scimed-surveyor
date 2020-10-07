#!/usr/bin/env python3

from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
import requests

search = 'covid-19'
baseurl = 'https://pubmed.ncbi.nlm.nih.gov'
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def save(doc):
    res = es.index(index='covid-19-articles', body=doc)
    print(res)

for page in range(3):
    url = '%s/?term=%s&show_snippets=off&sort=date&page=%i' % (baseurl, search, page)
    html = requests.get(url).text
    bs = BeautifulSoup(html, features='html.parser')
    links = bs.find_all('a', attrs={'class':'docsum-title'}, href=True)

    for link in links:
        url = baseurl + link['href']
        html = requests.get(url).text
        bs = BeautifulSoup(html, features='html.parser')
        title = bs.find('h1', attrs={'class':'heading-title'}).text.strip()
        abstract_tag = bs.find('div', attrs={'class':'abstract-content'})
        if not abstract_tag:
            continue
        abstract = abstract_tag.text.strip()
        print(url, '--', title, '--', abstract[:100]+'...')
        doc = {'url':url, 'title':title, 'abstract':abstract}
        save(doc)
