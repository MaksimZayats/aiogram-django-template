# Makefile Commands

Available make commands for development.

## Development

| Command | Description |
|---------|-------------|
| `make dev` | Start Django development server |
| `make celery-dev` | Start Celery worker with debug logging |
| `make celery-beat-dev` | Start Celery Beat scheduler |
| `make bot-dev` | Start Telegram bot |

### Usage

```bash
# Start API server (http://localhost:8000)
make dev

# In another terminal, start Celery worker
make celery-dev

# In another terminal, start Beat scheduler
make celery-beat-dev
```

## Database

| Command | Description |
|---------|-------------|
| `make makemigrations` | Create new database migrations |
| `make migrate` | Apply database migrations |
| `make collectstatic` | Collect static files |

### Usage

```bash
# After model changes
make makemigrations

# Apply migrations
make migrate
```

## Code Quality

| Command | Description |
|---------|-------------|
| `make format` | Format code with ruff |
| `make lint` | Run all linters |
| `make test` | Run tests with coverage |

### Usage

```bash
# Format code
make format

# Check code quality
make lint

# Run tests
make test
```

## Documentation

| Command | Description |
|---------|-------------|
| `make docs` | Serve documentation locally |
| `make docs-build` | Build documentation |

### Usage

```bash
# Serve docs at http://localhost:8000
make docs

# Build static site
make docs-build
```

## Command Details

### make dev

```makefile
dev:
	DJANGO_DEBUG=true uv run manage.py runserver
```

Starts Django development server with debug mode enabled.

### make celery-dev

```makefile
celery-dev:
	OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uv run celery -A delivery.tasks.app worker --loglevel=DEBUG
```

Starts Celery worker with:

- macOS fork safety workaround
- Debug log level

### make format

```makefile
format:
	uv run ruff format .
	uv run ruff check --fix-only .
```

Runs:

1. Ruff formatter
2. Ruff auto-fixes

### make lint

```makefile
lint:
	uv run ruff check .
	uv run ty check .
	uv run pyrefly check src/
	uv run mypy src/ tests/
```

Runs:

1. Ruff linter
2. ty type checker
3. pyrefly checker
4. mypy type checker

### make test

```makefile
test:
	uv run pytest tests/
```

Runs pytest with coverage requirements.

## Adding Custom Commands

Add to `Makefile`:

```makefile
# Custom command
my-command:
	uv run python my_script.py

.PHONY: my-command
```
