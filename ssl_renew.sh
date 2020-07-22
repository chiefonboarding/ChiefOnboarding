#!/bin/bash

docker-compose -f docker-compose.production.yml --no-ansi run certbot renew
docker restart web
docker restart nginx
