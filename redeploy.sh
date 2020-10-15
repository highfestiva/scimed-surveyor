#!/bin/bash

docker-compose build
export COMMIT=`git rev-parse --short HEAD`
docker-compose up -d
