#!/usr/bin/env python3

import argparse
from collections import defaultdict
from elasticsearch import Elasticsearch
from extra_annotations import extra_annotations
import json
import re


tag_split = re.compile(r'[^#a-z0-9]')
term2topic_name = {}
word2terms = defaultdict(set) # optimization


def read_tweet(text, options):
    tweet = json.loads(text)
    text = tweet['text'].strip('…').lower()
    tweet['date'] = tweet['created_at'].partition(':')[0] + 'Z'
    annotations = {'hashtag': list(filter(lambda s:s, [w for w in tag_split.split(text) if w and w[0]=='#']))}
    for topic,terms in extra_annotations.items():
        for term in terms:
            if term in text and re.search(r'\b%s\b'%term, text):
                if topic not in annotations:
                    annotations[topic] = []
                annotations[topic].append(term)
    for word in text.split():
        terms = word2terms.get(word, [])
        for term in terms:
            if term in text:
                for ch in '()[]':
                    term = term.replace('(','\\'+ch)
                if re.search(r'\b%s\b'%term, text):
                    topic,_,term = term2topic_name[term].partition(':')
                    if topic not in annotations:
                        annotations[topic] = []
                    annotations[topic].append(term)
                    if 'Tyr' in term:
                        print('"%s" "%s" %s' % (word, term, annotations))
    tweet['annotations'] = annotations
    return tweet


parser = argparse.ArgumentParser()
parser.add_argument('--reset-index', action='store_true', default=False, help='delete index before inserting anything new')
parser.add_argument('--index', required=True, help='index to insert into, e.g. "twitter-health-19"')
options = parser.parse_args()


print('loading mesh files...')
for fname,topic,heads in [('c2020.bin','chemical',('NM =','SY =')), ('d2020.bin','term',('MH =','ENTRY =')), ('q2020.bin','field',('SH = ','QX ='))]:
    for line in open('data/'+fname, encoding='utf8'):
        for i,head in enumerate(heads):
            if line.startswith(head):
                term = line.partition(' = ')[2].partition('|')[0].strip()
                if i == 0:
                    main_term = term
                if len(term) <= 5:
                    continue
                term = term.lower()
                if 'covid' in term or 'corona' in term:
                    continue
                term2topic_name[term] = topic+':'+main_term
                word = term.partition(' ')[0]
                word = word if word[-1]!=',' else word[:-1]
                word2terms[word].add(term)
print('term list size:', len(term2topic_name))


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
