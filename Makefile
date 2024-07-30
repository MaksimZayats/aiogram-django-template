run.bot:
	python -m bot

run.server.local:
	sh ./run-local.sh

run.server.prod:
	python -m gunicorn api.web.wsgi:application \
		--bind 0.0.0.0:80 \
		--workers ${WORKERS} \
		--threads ${THREADS} \
		--timeout 480

run.bot.local:
	python -m bot

run.bot.prod:
	python -m bot

run.celery.local:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES celery -A tasks.app worker --loglevel=DEBUG

run.celery.prod:
	celery -A tasks.app worker --loglevel=INFO

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

collectstatic:
	python manage.py collectstatic --no-input

createsuperuser:
	python manage.py createsuperuser --email "" --username admin

# Tests, linters & formatters
fmt:
	make -k ruff-fmt black

lint:
	make -k ruff black-check mypy

black:
	python -m black .

black-check:
	python -m black --check .

ruff:
	python -m ruff check .

ruff-fmt:
	python -m ruff --fix-only --unsafe-fixes .

test:
	python -m pytest

mypy:
	python -m mypy .
