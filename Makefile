ENV ?= local
ENV_FILE := .env

COMPOSE := docker compose \
	--env-file $(ENV_FILE) \
	--file docker/docker-compose.yaml \
	--file docker/overrides/docker-compose.$(ENV).yaml

COMPOSE_INFRA := docker compose \
	--env-file $(ENV_FILE) \
	--file docker/docker-compose.infra.yaml \
	--file docker/overrides/docker-compose.$(ENV).yaml

dev:
	DJANGO_DEBUG=true uv run manage.py runserver

makemigrations:
	uv run manage.py makemigrations

migrate:
	uv run manage.py migrate

collectstatic:
	uv run manage.py collectstatic --no-input

format:
	uv run ruff format .
	uv run ruff check --fix-only .

lint:
	uv run ruff check .
	uv run ty check .
	uv run pyrefly check src/
	uv run --env-file .env.test mypy src/ tests/

test:
	uv run --env-file .env.test pytest tests/

docker-build:
	$(COMPOSE) build builder

docker-up:
	$(COMPOSE) up -d

docker-down:
	$(COMPOSE) down

docker-infra-up:
	$(COMPOSE_INFRA) up -d

docker-infra-down:
	$(COMPOSE_INFRA) down
