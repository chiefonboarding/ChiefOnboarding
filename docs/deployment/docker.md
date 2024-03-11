# Deploy with Docker
You can easily deploy ChiefOnboarding with Docker (Docker-compose). Make sure that both Docker and Docker-compose are installed and your server. Please note that some of the data below contain example values and should be replaced.

1. Point your domain name to your IP address.
2. Create a folder somewhere and then add this `docker-compose.yml` file (change the environment variables to something that works for you!):

## Caddy-based deployment

```yaml
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
      - DATABASE_URL=postgres://postgres:postgres@db:5432/chiefonboarding
      - ALLOWED_HOSTS=test.chiefonboarding.com
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
If you don't want to have a secure connecting and want to connect over `http` (not secure, and you will have to change the Caddy file below), then add `HTTP_INSECURE=True` to your environment variables.

Then we need to create a `Caddyfile` to route the requests to the server (change the domain name, obviously):
```ini
test.chiefonboarding.com {
  reverse_proxy web:8000
}
```
## Non-caddy-based deployment
This method may make it easier to deploy on a server that is already configured with an existing web server (e.g., Nginx, Apache, etc.) You will need to install Cerbot to configure LetsEncrypt. This approach assumes that you will be configuring a reverse proxy on port 8888.

```yaml
version: '3'

services:
  db:
    image: postgres:latest
    restart: always
    volumes:
      - /var/chiefonboarding/pg_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=chiefonboarding
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres

  app:
    image: chiefonboarding/chiefonboarding:latest
    restart: always
    ports:
      - "8888:8000"
    environment:
      - SECRET_KEY=somethingsupersecret
      - DATABASE_URL=postgres://postgres:postgres@db:5432/chiefonboarding
      - ALLOWED_HOSTS=test.chiefonboarding.com
    depends_on:
      - db
```
3. You can now run docker compose: `docker-compose up`. When you go to your domain name, you should see a login form where you can fill in your username and password (either from the logs, or specified yourself). There will be some demo data in there already, feel free to delete everything. 

> Note: if you need to do a healthcheck for your container, then you can use the url `/health` for that. This url is available under any IP/domain name. It will respond with a 200 status and an `ok` as content. The `ALLOWED_HOSTS` variable is ignored for that url.

## Update docker image
Please make a backup of your database before doing this.  

1. First stop all containers: `docker-compose down`
2. Pull the new image: `docker-compose pull`
3. Start the containers: `docker-compose up -d`
