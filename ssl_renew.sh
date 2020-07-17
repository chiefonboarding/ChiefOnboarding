#!/bin/bash

docker-compose --no-ansi run certbot renew
docker-compose --no-ansi kill -s SIGHUP web

