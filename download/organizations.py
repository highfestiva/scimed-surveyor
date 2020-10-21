import re
import spacy


nlp = spacy.load('en_core_web_sm')
ent_split = re.compile(r'[^a-z0-9\-\. &]')


def extract(text):
    orgs = set()
    for ent in nlp(text).ents:
        if ent.label_ != 'ORG':
            continue
        text = ent.text.lower().replace('&amp', '&').replace('&gt', '>')
        if '#' in text or 'http' in text:
            continue
        text = ' '.join([w for w in ent_split.split(text) if w]).strip(' &-.')
        if len(text) <= 2:
            continue
        orgs.add(text)
    return orgs
