#!/usr/bin/env bash

MONGODB_URI=`heroku config:get MONGODB_URI`
REDIS_URL=`heroku config:get REDIS_URL`

docker run -p 5556:5555 -e MONGODB_URI=${MONGODB_URI} -e REDIS_URL=${REDIS_URL} \
       sportsfreund_worker_dashboard mrq-dashboard
