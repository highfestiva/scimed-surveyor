#!/bin/bash

export COMMIT=`git rev-parse --short HEAD`
docker-compose build
docker-compose up -d
