#!/bin/bash

cp download/journal_util.py download/.espassword http-server/
cp download/*twitter*.py download/.twitter*.py download/.espassword download/autoupdate/

export COMMIT=`git rev-parse --short HEAD`
docker-compose build
docker-compose up -d
