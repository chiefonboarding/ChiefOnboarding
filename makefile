local:
	docker compose up

migrate:
	docker compose run --rm web uv run python manage.py migrate

makemigrations:
	docker compose run --rm web uv run python manage.py makemigrations

shell:
	docker compose run --rm web uv run python manage.py shell

test:
	docker compose run --rm web uv run pytest

bash:
	docker compose run --rm web bash

build:
	docker compose build web

lock:
	docker compose run --rm web uv lock

format:
	docker compose run --rm web uv run ruff format .
	docker compose run --rm web uv run ruff check . --fix
