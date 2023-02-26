#!/bin/zsh

docker-compose build
docker-compose up -d
docker stop a_plus_tsukuba-web-1