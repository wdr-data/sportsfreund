#!/usr/bin/env bash
docker-compose start
docker-compose logs -f
docker-compose stop
echo "Bye!"
