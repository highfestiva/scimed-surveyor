#!/bin/bash

docker network create backend
docker stop elastic
docker rm elastic
docker pull docker.elastic.co/elasticsearch/elasticsearch:7.9.2
docker run -d --name elastic --network backend --net-alias elastic -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.9.2
