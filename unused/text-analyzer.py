#!/usr/bin/env python3

import nltk

nltk.download('abc')
nltk.download('smultron')

# from nltk import smultron
from nltk.corpus import abc

print(abc)
print(dir(abc))
print(abc.words())

print(sv)
print(dir(sv))

print(sv.words())
sv.demo()

# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')

sentence = 'Ibland hoppar Jonas upp ur sängen som en gasell, redo att tackla världen med hela sin makt.'
tokens = nltk.word_tokenize(sentence)
print(tokens)
tagged = nltk.pos_tag(tokens)
print(tagged)
