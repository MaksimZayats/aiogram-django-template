dev:
	DJANGO_DEBUG=true uv run src/manage.py runserver

makemigrations:
	uv run src/manage.py makemigrations

migrate:
	uv run src/manage.py migrate

collectstatic:
	uv run src/manage.py collectstatic --no-input

format:
	uv run ruff format .
	uv run ruff check --fix-only .

lint:
	uv run ruff check .
	uv run ty check .
	uv run pyrefly check src/
	uv run mypy src/ tests/

test:
	uv run pytest tests/

celery-dev:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uv run watchmedo auto-restart \
		--directory=src \
		--pattern='*.py' \
		--recursive \
		-- celery -A delivery.tasks.app worker --loglevel=DEBUG

celery-beat-dev:
	uv run watchmedo auto-restart \
		--directory=src \
		--pattern='*.py' \
		--recursive \
		-- celery -A delivery.tasks.app beat --loglevel=DEBUG

bot-dev:
	uv run watchmedo auto-restart \
		--directory=src \
		--pattern='*.py' \
		--recursive \
		-- python -m delivery.bot

.PHONY: docs docs-build
docs:
	uv run mkdocs serve --livereload -f docs/mkdocs.yml

docs-build:
	uv run mkdocs build -f docs/mkdocs.yml
