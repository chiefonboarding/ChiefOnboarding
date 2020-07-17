curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs

npm install -g npm@latest

# generate Nuxt output
cd front
npm install
npm run postinstall
cd ../

# Replace the values in the env file and the nginx conf file
randval=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

sed -e "s/%1/$1/g" -e "s/%2/$randval/g" ./prod.env.example > ./prod.env 

#sed "s/%host/$1/g" ./nginx/django_project.example > ./nginx/sites-enabled/django_project
sed "s/%host/$1/g" ./nginx/django_project_ssl.example > ./nginx/sites-enabled/django_project_ssl

mkdir back/staticfiles

docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up
