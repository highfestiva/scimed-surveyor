#!/usr/bin/env python3

import json
import spacy

nlp = spacy.load('en_core_web_sm')
for line in open('../download/data/twitter.json'):
    tweet = json.loads(line)['text']
    for ent in nlp(tweet).ents:
        print(ent.text, ent.label_, end=' ~ ')
    print()
    print()
