curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -
sudo apt-get install -y nodejs

npm install -g npm@latest

# generate Nuxt output
cd front
npm install
npm run postinstall
cd ../

# rewrite url in nginx conf file
sed "s/localhost/$1/g" ./nginx/sites-enabled/django_project

# add environment variables
export BASE_URL=$1
export ALLOWED_HOSTS=$1
export DEBUG=False
export SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

mkdir back/staticfiles

docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up
