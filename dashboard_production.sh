#!/usr/bin/env bash

MONGODB_URI=`heroku config:get MONGODB_URI`
REDIS_URL=`heroku config:get REDIS_URL`

docker-compose build worker_dashboard
docker run -it -p 127.0.0.1:5556:5555 -e MONGODB_URI=${MONGODB_URI} -e REDIS_URL=${REDIS_URL} -e SECRET_KEY=1 \
       sportsfreund_worker_dashboard mrq-dashboard
