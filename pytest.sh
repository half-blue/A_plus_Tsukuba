#!/bin/zsh

docker-compose build
docker-compose up -d
docker exec a_plus_tsukuba-web-1 pytest