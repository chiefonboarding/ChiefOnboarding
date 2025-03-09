local:
	docker compose up

migrate:
	docker compose run --rm web python manage.py migrate

makemigrations:
	docker compose run --rm web python manage.py makemigrations

shell:
	docker compose run --rm web python manage.py shell

test:
	docker compose run --rm web pytest

bash:
	docker compose run --rm web bash

build:
	docker compose build web

lock:
	docker compose run --rm web pipenv lock

format:
	docker compose run --rm web ruff format .
	docker compose run --rm web ruff check . --fix
