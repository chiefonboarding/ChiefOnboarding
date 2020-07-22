#!/usr/bin/env bash

if [[ -z "$1" || -z "$2" ]]; then
    echo -e "\nPlease call '$0 <base_url> <email_address>' to run this command!\n"
    exit 1
fi

export BASE_URL=$1
export BASE_EMAIL=$2
# Replace the values in the env file and the nginx conf file
randval=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

sed -i "s/process.env.BASE_URL/'https:\/\/$1'/g" ./front/nuxt.config.js
sed -e "s/%1/$1/g" -e "s/%2/$randval/g" ./prod.env.example > ./back/back/.env 

# Generate dhparam file
openssl dhparam -out ./certbot/dhparam/dhparam-2048.pem 2048
mkdir -p ./nginx/sites-enabled/
sed "s/%host/$1/g" ./nginx/django_project_ssl.example > ./nginx/sites-enabled/django_project_ssl.conf

docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up
