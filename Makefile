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
	uv run pytest tests/

celery-dev:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uv run celery -A tasks.app worker --loglevel=DEBUG

.PHONY: docs docs-build
docs:
	uv run mkdocs serve --livereload -f docs/mkdocs.yml

docs-build:
	uv run mkdocs build -f docs/mkdocs.yml
