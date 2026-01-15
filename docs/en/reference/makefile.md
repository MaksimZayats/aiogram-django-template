# Makefile Commands

All development commands are available through the Makefile.

## Development Server

| Command | Description |
|---------|-------------|
| `make dev` | Run Django development server with `DJANGO_DEBUG=true` |
| `make celery-dev` | Run Celery worker with DEBUG logging |
| `make celery-beat-dev` | Run Celery beat scheduler with DEBUG logging |
| `make bot-dev` | Run Telegram bot in polling mode |

## Database

| Command | Description |
|---------|-------------|
| `make makemigrations` | Create new database migrations |
| `make migrate` | Apply pending database migrations |

## Static Files

| Command | Description |
|---------|-------------|
| `make collectstatic` | Collect static files to storage backend |

## Code Quality

| Command | Description |
|---------|-------------|
| `make format` | Format code with ruff and apply auto-fixes |
| `make lint` | Run all linters: ruff, ty, pyrefly, mypy |
| `make test` | Run pytest test suite |

## Documentation

| Command | Description |
|---------|-------------|
| `make docs` | Serve documentation locally with live reload |
| `make docs-build` | Build documentation for deployment |

## Command Details

### make dev

```bash
DJANGO_DEBUG=true uv run src/manage.py runserver
```

Starts the Django development server on `http://127.0.0.1:8000`.

### make celery-dev

```bash
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uv run celery -A delivery.tasks.app worker --loglevel=DEBUG
```

The `OBJC_DISABLE_INITIALIZE_FORK_SAFETY` flag is required on macOS.

### make celery-beat-dev

```bash
uv run celery -A delivery.tasks.app beat --loglevel=DEBUG
```

Runs the periodic task scheduler.

### make bot-dev

```bash
uv run python -m delivery.bot
```

Runs the Telegram bot in long-polling mode. Requires `TELEGRAM_BOT_TOKEN`.

### make format

```bash
uv run ruff format .
uv run ruff check --fix-only .
```

Formats code and applies safe auto-fixes.

### make lint

```bash
uv run ruff check .
uv run ty check .
uv run pyrefly check src/
uv run mypy src/ tests/
```

Runs the complete linting pipeline:

| Tool | Purpose |
|------|---------|
| ruff | Fast Python linter |
| ty | Type linter |
| pyrefly | Additional static analysis |
| mypy | Type checker |

### make test

```bash
uv run pytest tests/
```

Runs the test suite. Configure coverage requirements in `pyproject.toml`.

### make docs

```bash
uv run mkdocs serve --livereload -f docs/mkdocs.yml
```

Serves documentation at `http://127.0.0.1:8000` with auto-reload.

### make docs-build

```bash
uv run mkdocs build -f docs/mkdocs.yml
```

Builds static documentation to `docs/site/`.
