#!/usr/bin/env bash
docker-compose build
docker-compose up -d
docker-compose logs -f
docker-compose stop
echo "Bye!"
