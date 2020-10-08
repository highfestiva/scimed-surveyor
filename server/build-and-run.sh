#!/bin/bash


cd scimed-surveyor-server
docker stop scimed-surveyor-server
docker rm scimed-surveyor-server
docker build -t scimed-surveyor-server .
docker run -d --name scimed-surveyor-server --network backend --net-alias scimed-surveyor-server --restart unless-stopped scimed-surveyor-server

cd ../nginx
docker stop nginx-scimed
docker rm nginx-scimed
docker build -t nginx-scimed .
docker run -d --name nginx-scimed  --restart unless-stopped -p 8080:80 --link glance:glance nginx-scimed
