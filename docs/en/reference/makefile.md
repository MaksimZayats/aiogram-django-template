# Makefile Commands

Reference for all available Make targets.

## Development

### `make dev`

Start the Django development server with auto-reload.

```bash
make dev
# Equivalent to: uv run python src/manage.py runserver
```

Access at [http://localhost:8000](http://localhost:8000)

### `make celery-dev`

Start Celery worker with auto-reload for development.

```bash
make celery-dev
# Equivalent to: uv run celery -A delivery.tasks.app worker --loglevel=info
```

### `make shell`

Open Django interactive shell.

```bash
make shell
# Equivalent to: uv run python src/manage.py shell
```

## Database

### `make migrate`

Apply pending database migrations.

```bash
make migrate
# Equivalent to: uv run python src/manage.py migrate
```

### `make makemigrations`

Create new migration files for model changes.

```bash
make makemigrations
# Equivalent to: uv run python src/manage.py makemigrations
```

### `make showmigrations`

Show all migrations and their status.

```bash
make showmigrations
# Equivalent to: uv run python src/manage.py showmigrations
```

## Code Quality

### `make format`

Format code with ruff (auto-fix issues).

```bash
make format
# Equivalent to: uv run ruff format src tests && uv run ruff check src tests --fix
```

### `make lint`

Run all linters without auto-fixing.

```bash
make lint
# Runs: ruff, ty, pyrefly, mypy
```

### `make check`

Run all quality checks (format check + lint).

```bash
make check
```

## Testing

### `make test`

Run the full test suite with coverage.

```bash
make test
# Equivalent to: uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

### `make test-fast`

Run tests without coverage (faster).

```bash
make test-fast
# Equivalent to: uv run pytest
```

### `make test-verbose`

Run tests with verbose output.

```bash
make test-verbose
# Equivalent to: uv run pytest -v
```

## Docker

### `make docker-up`

Start all Docker services.

```bash
make docker-up
# Equivalent to: docker compose up -d
```

### `make docker-down`

Stop all Docker services.

```bash
make docker-down
# Equivalent to: docker compose down
```

### `make docker-logs`

View logs from Docker services.

```bash
make docker-logs
# Equivalent to: docker compose logs -f
```

### `make docker-build`

Build Docker images.

```bash
make docker-build
# Equivalent to: docker compose build
```

## Dependencies

### `make install`

Install all dependencies.

```bash
make install
# Equivalent to: uv sync --locked --all-extras --dev
```

### `make update`

Update dependencies to latest compatible versions.

```bash
make update
# Equivalent to: uv sync --all-extras --dev
```

### `make lock`

Regenerate lock file.

```bash
make lock
# Equivalent to: uv lock
```

## Cleaning

### `make clean`

Remove build artifacts and cache files.

```bash
make clean
# Removes: __pycache__, .pytest_cache, .mypy_cache, .ruff_cache, etc.
```

### `make clean-docker`

Remove Docker volumes and orphan containers.

```bash
make clean-docker
# Equivalent to: docker compose down -v --remove-orphans
```

## Help

### `make help`

Show available targets with descriptions.

```bash
make help
```

## Common Workflows

### Starting Fresh

```bash
# Clone and setup
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template
make install
cp .env.example .env

# Start services
make docker-up
make migrate

# Run application
make dev  # Terminal 1
make celery-dev  # Terminal 2
```

### Before Committing

```bash
# Format and check
make format
make lint
make test
```

### After Model Changes

```bash
make makemigrations
make migrate
```

### Full Reset

```bash
make clean
make clean-docker
make docker-up
make migrate
```

## Environment-Specific Commands

Some commands respect environment variables:

```bash
# Use specific settings
DJANGO_SETTINGS_MODULE=core.configs.production make migrate

# Override database
DATABASE_URL=postgres://... make migrate
```

## Related

- [Environment Variables](environment-variables.md) - Configuration options
- [Docker Services](docker-services.md) - Container details
- [Quick Start](../getting-started/quick-start.md) - Getting started guide
