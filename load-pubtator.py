#!/usr/bin/env python3

from json import loads

lines = []
for line in open('litcovid2pubtator.json'):
    if '"_id": ' in line[:15]:
        print('---------------------')
        line = loads(line[1:])
        annotations = set()
        title = False
        for passage in line['passages']:
            if not title and passage['infons']['type'] in ('front','title'):
                title = True
                print('~', passage['infons']['type'], passage['text'])
            if 'annotations' in passage:
                for a in passage['annotations']:
                    annotations.add(a['infons']['type'] + ':' + a['text'])
        print('  ', annotations)
        # print(line)
        lines.append(line)
        if len(lines) == 50:
            break

print('looked through %i articles' % len(lines))
