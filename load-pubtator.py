#!/usr/bin/env python3

from collections import defaultdict
from json import loads
import re

journal_split_regexp = re.compile(r'[\.;,]')
date_match = re.compile(r'(19\d\d|20\d\d)')
date_end_fix = re.compile(r'[A-Za-z]{3}[-/]([A-Za-z]{3})')
date_pick = re.compile(r'(\d{4}) .*?([A-Z][a-z]{2}|\d\d)\s*(\d{1,2}|)\b.*')
date_replacements = {   ' / ': '/',
                        ' - ': '-',
                        'Spring': 'May',
                        'Summer': 'Aug',
                        'Autumn': 'Nov',
                        'Winter': 'Feb'     }
mon_replacements = {mon.title():str(i+1) for i,mon in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split())}

articles = []
for line in open('litcovid2pubtator.json'):
    if '"_id": ' in line[:15]:
        # print('---------------------')
        line = loads(line[1:])
        title = ''
        date = None
        annotations = defaultdict(set)
        for passage in line['passages']:
            if not title and passage['infons']['type'] in ('front','title'):
                title = passage['text']
                if 'journal' in passage['infons']:
                    journal = passage['infons']['journal']
                    dates = [s.strip() for s in journal_split_regexp.split(journal)]
                    dates = [s for s in dates if date_match.match(s)]
                    if dates:
                        date = dates[0]
                        for k,v in date_replacements.items():
                            date = date.replace(k,v)
                        date = date_end_fix.sub(r'\1', date)
                        year,month,day = [date_pick.sub(r'\%i'%i, date) for i in range(1,3+1)]
                        for k,v in mon_replacements.items():
                            month = month.replace(k,v)
                        date = year + ('-%.2i'%int(month) if month else '') + ('-%.2i'%int(day) if day else '')
            if 'annotations' in passage:
                for a in passage['annotations']:
                    annotations[a['infons']['type'].lower()].add(a['text'].lower())
        article = {'date':date, 'title':title, **annotations}
        articles.append(article)
        if len(articles) == 500:
            break

for article in articles:
    print(article['date'], '~', article['title'], '~', {k:v for k,v in article.items() if k not in ('date', 'title')})

print('looked through %i articles' % len(articles))
