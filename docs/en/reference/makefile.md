# Makefile Commands

All development commands are available through the Makefile.

## Development Server

| Command | Description |
|---------|-------------|
| `make dev` | Run FastAPI development server with uvicorn (hot reload) |
| `make celery-dev` | Run Celery worker with DEBUG logging and auto-restart |
| `make celery-beat-dev` | Run Celery beat scheduler with DEBUG logging |

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
uv run uvicorn delivery.http.app:app --reload --host 0.0.0.0 --port 8000
```

Starts the FastAPI development server on `http://0.0.0.0:8000` with hot reload.

### make celery-dev

```bash
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uv run watchmedo auto-restart \
    --directory=src \
    --pattern='*.py' \
    --recursive \
    -- celery -A delivery.tasks.app worker --loglevel=DEBUG
```

Uses `watchmedo` to auto-restart the worker on code changes. The `OBJC_DISABLE_INITIALIZE_FORK_SAFETY` flag is required on macOS.

### make celery-beat-dev

```bash
uv run celery -A delivery.tasks.app beat --loglevel=DEBUG
```

Runs the periodic task scheduler.

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
