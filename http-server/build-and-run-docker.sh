#!/bin/bash

docker stop scimed-surveyor-server
docker rm scimed-surveryor-server
docker build -t scimed-surveryor-server .
docker run -d --name scimed-surveryor-server --restart unless-stopped -p 8080:8080 scimed-surveryor-server
