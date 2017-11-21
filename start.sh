#!/usr/bin/env bash
docker-compose build
docker-compose start
docker-compose logs -f
docker-compose stop
echo "Bye!"
