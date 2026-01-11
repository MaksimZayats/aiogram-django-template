dev:
	DJANGO_DEBUG=true uv run --env-file .env manage.py runserver

makemigrations:
	uv run --env-file .env manage.py makemigrations

migrate:
	uv run --env-file .env manage.py migrate

collectstatic:
	uv run --env-file .env manage.py collectstatic --no-input

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
