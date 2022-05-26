---
order: 80
---

# Deployment
Currently, two ways of deploying are supported out of the box. Docker and Heroku.

1. [Deploy with Docker](#deploy-with-docker)
2. [Deploy with Render](#deploy-with-render)
3. [Deploy with Heroku](#deploy-with-heroku)

### Deploy with Docker
You can easily deploy ChiefOnboarding with Docker (Docker-compose). Make sure that both Docker and Docker-compose are installed and your server. Please note that some of the data below contain example values and should be replaced.

1. Point your domain name to your IP address.
2. Create a folder somewhere and then add this `docker-compose.yml` file (change the environment variables to something that works for you!):

```
version: '3'

services:
  db:
    image: postgres:latest
    restart: always
    expose:
      - "5432"
    volumes:
      - pgdata:/var/lib/postgresql/data/
    environment:
      - POSTGRES_DB=chiefonboarding
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    networks:
      - global

  web:
    image: chiefonboarding/chiefonboarding:latest
    restart: always
    expose:
      - "8000"
    environment:
      - SECRET_KEY=somethingsupersecret
      - BASE_URL=https://test.chiefonboarding.com
      - DATABASE_URL=postgres://postgres:postgres@db:5432/chiefonboarding
      - ALLOWED_HOSTS=test.chiefonboarding.com
      - DEFAULT_FROM_EMAIL=hello@chiefonboarding.com
    depends_on:
      - db
    networks:
      - global

  caddy:
    image: caddy:2.3.0-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - $PWD/Caddyfile:/etc/caddy/Caddyfile
      - $PWD/site:/srv
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - global

volumes:
  pgdata:
  caddy_data:
  caddy_config:

networks:
  global:

```
A quick note: it will generate an account for you. Please check the logs for that (you can and should delete this account after you created a new admin account). If you want to specify your own login details, then specify a `ACCOUNT_EMAIL` (should always be lowercase email address) and `ACCOUNT_PASSWORD` in the environment variables.
Second note: if you need to do a healthcheck for your container, then you can use the url `/health` for that. This url is available under any IP/domain name. It will respond with a 200 status and an `ok` as content. The `ALLOWED_HOSTS` variable is ignored for that url.

If you don't want to have a secure connecting and want to connect over `http` (not secure, and you will have to change the Caddy file below), then add `HTTP_INSECURE=True` to your environment variables.

3. Then we need to create a `Caddyfile` to route the requests to the server (change the domain name, obviously):
```
test.chiefonboarding.com {
  reverse_proxy web:8000
}
```
5. You can now run docker compose: `docker-compose up`. When you go to your domain name, you should see a login form where you can fill in your username and password (either from the logs, or specified yourself). There will be some demo data in there already, feel free to delete everything. 

#### Updating docker image
Please make a backup of your database before doing this.  

1. First stop all containers: `docker-compose down`
2. Pull the new image: `docker-compose pull`
3. Start the containers: `docker-compose up -d`

### Deploy with Render
You will have to login to Render or create an account there. Then, you will need to click this link to start the process: [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/chiefonboarding/chiefonboarding/) 

You will then need to fill in the following details:

**ACCOUNT_EMAIL**: This is the email address from the first admin account. Don't worry, you can add more accounts later and delete this one.

**ACCOUNT_PASSWORD**: Fill in your prefered password. Anything works, but please make it long.

**ALLOWED_HOSTS**: This needs to be the domain you want to use for the platform. Either your Render subdomain or your own subdomain. You can add multiple urls if you want to make it available with multiple urls (example: `domain.example.com,domain2.example.com`). Do **not** add the protocol (`https://`) before the url. If you don't have a url, use `test.chiefonboarding.com` and change it later to your `xxxx.onrender.com` link.

Click on deploy and let it run. This will take about 10 minutes before it's ready, though it could take a few hours, so be patient please. 

**If you DO have a domain name**:

Go to the `chiefonboarding` service and go to `settings`. Scroll down until you see the `Custom domain` setting. Add your domain there and configure your DNS to link to it.

**If you DO NOT have a domain name**:

Go to environment variables and swap the `ALLOWED_HOSTS` and `BASE_URL` with the url that has been given to you by Render. Wait for it to automatically redeploy.

That's all!

### Deploy with Heroku
Please note: you will need to have an account at Heroku for this to work. Hosting at Heroku is more expensive than hosting it with Docker on a VPS. We will set it up to use two Hobby Dynos (which will be $14/month). A database upgrade might be necessary later on.

You will have to login to Heroku or create an account there. Then, you will need to click this link to start the process: [https://heroku.com/deploy?template=https://github.com/chiefonboarding/ChiefOnboarding](https://heroku.com/deploy?template=https://github.com/chiefonboarding/ChiefOnboarding).
Heroku will then ask you for some details. Please be careful to put them in correctly, otherwise your app will not start.

The **app name** can be anything you want (so long it is available).

Under "config vars" you will have 5 items. Before you fill in anything: decide whether you want to use a Heroku subdomain `<app name>.herokuapp.com` or your own domain `onboarding.yourcompany.com`. Your own domain doesn't have to be a subdomain.

**ACCOUNT_EMAIL**: This is the email address from the first admin account. Don't worry, you can add more accounts later and delete this one.

**ACCOUNT_PASSWORD**: You can't change this, it is automatically generated by Heroku. Once the app deployed, go to setting -> environment variables. Click on 'reveal' and copy the password that's generated. That, with your email address should allow you to login.

**SECRET_KEY**: You can't change this and shouldn't. It will be generated by Heroku. It's used for signing cookies, encrypting data etc.

**SSL_REDIRECT**: Leave it at `True`. This is used to redirect all traffic from `http` to `https`. 

**ALLOWED_HOSTS**: This needs to be the domain you want to use for the platform. Either your Heroku subdomain or your own subdomain. You can add multiple urls if you want to make it available with multiple urls (example: `domain.example.com,domain2.example.com`). Do **not** add the protocol (`https://`) before the url.

Click on `Deploy app`. You should see this when it's done (this might take a few minutes):

![heroku deploy done](static/heroku-deploy-done.png)

If you are using a custom domain: go to the settings area and look for the 'domains' part:

![heroku settings domain](static/heroku-settings-domain.png)

Then click on 'Add domain' and enter your domain name. You will get a DNS target to point your domain name to in your DNS settings:

![heroku new domain](static/heroku-new-domain.png)

You might get a red icon now next to your domain name. It might take a bit of time to get your domain validated (DNS is often cached). Just wait for a bit and try to refresh it until it becomes green:

![heroku click recheck](static/heroku-click-recheck.png)

That's all!

#### Update Heroku 
Please make a backup of your database before doing this.

1. Install the Heroku CLI and authenticate yourself.
2. Download the ChiefOnboarding git repo: `git clone https://github.com/chiefonboarding/ChiefOnboarding.git`
3. Add your heroku git url as a git remote. You can find this url on the app's settings page -> app info -> Heroku git URL. `git remote add heroku_repo repo_url` (replace `repo_url` with your own url).
4. Then push it up: `git push heroku_repo master`
