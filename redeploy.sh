#!/bin/bash

cp download/journal_util.py download/.espassword http-server/
cp download/*.py download/.twitterkey.py download/.espassword download/autoupdate/
cp download/data/?202?.bin download/autoupdate/data/

export COMMIT=`git rev-parse --short HEAD`
docker-compose build
docker-compose up -d
