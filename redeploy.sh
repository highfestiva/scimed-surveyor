#!/bin/bash

cp download/journal_util.py http-server/

export COMMIT=`git rev-parse --short HEAD`
docker-compose build
docker-compose up -d
