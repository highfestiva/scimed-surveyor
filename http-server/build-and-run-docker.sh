#!/bin/bash

docker stop scimed-surveyor-server
docker rm scimed-surveyor-server
docker build -t scimed-surveyor-server .
docker run -d --name scimed-surveyor-server --network backend --restart unless-stopped -p 8080:8080 scimed-surveyor-server
