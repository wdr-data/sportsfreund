#!/usr/bin/env bash
docker-compose build
docker-compose up -d
docker-compose logs -f web web-migrate worker localtunnel
docker-compose stop
echo "Bye!"
