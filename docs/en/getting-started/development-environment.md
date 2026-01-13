# Development Environment

Complete setup for local development.

## Package Manager (uv)

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

### Common Commands

```bash
# Install all dependencies
uv sync --locked --all-extras --dev

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Update lockfile
uv lock
```

## Infrastructure Services

The application requires PostgreSQL, Redis, and MinIO. Use Docker Compose for local development.

!!! tip "COMPOSE_FILE"
    The `.env.example` includes `COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml` which automatically configures Docker Compose for local development. Copy it to `.env` before running commands.

```bash
# Start PostgreSQL, Redis, and MinIO
docker compose up -d postgres redis minio

# Create MinIO buckets, run migrations, and collect static files
docker compose up minio-create-buckets migrations collectstatic

# View logs
docker compose logs -f postgres redis minio

# Stop services
docker compose down

# Stop and remove volumes (reset data)
docker compose down -v
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Broker |
| MinIO API | 9000 | S3-compatible storage |
| MinIO Console | 9001 | Web UI |

## Running the Application

### HTTP API

```bash
make dev
```

The server runs at `http://localhost:8000` with hot reload enabled.

### Celery Worker

```bash
make celery-dev
```

Runs with debug logging and auto-restart on file changes.

### Celery Beat (Scheduler)

```bash
make celery-beat-dev
```

### Telegram Bot

```bash
make bot-dev
```

Requires `TELEGRAM_BOT_TOKEN` in `.env`.

## Code Quality

### Formatting

```bash
make format
```

Uses [Ruff](https://docs.astral.sh/ruff/) for formatting and import sorting.

### Linting

```bash
make lint
```

Runs multiple linters:

- **ruff** — Fast Python linter
- **ty** — Type inference checker
- **pyrefly** — Additional static analysis
- **mypy** — Type checking

### Testing

```bash
make test
```

Runs pytest with 80% coverage requirement.

## IDE Configuration

### VS Code

Recommended extensions:

- Python (Microsoft)
- Ruff
- Pylance

Settings (`.vscode/settings.json`):

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit"
        }
    }
}
```

### PyCharm

1. Set interpreter to `.venv/bin/python`
2. Enable Ruff plugin
3. Configure Ruff as the formatter:
   - Settings → Tools → Ruff → Enable "Format on save"

## Database Operations

### Create Migrations

```bash
make makemigrations
```

### Apply Migrations

```bash
make migrate
```

### Django Shell

```bash
uv run manage.py shell
```

### Create Superuser

```bash
uv run manage.py createsuperuser
```

## Environment Variables

The application uses `.env` for local development. See [Environment Variables Reference](../reference/environment-variables.md) for all options.

### Test Environment

Tests use `.env.test` which is automatically loaded by pytest:

```bash
# .env.test
DATABASE_URL="postgres://postgres:test@localhost:5432/test_db"
```

## Troubleshooting

### Database Connection Failed

```
django.db.utils.OperationalError: could not connect to server
```

Ensure PostgreSQL is running:

```bash
docker compose ps postgres
docker compose logs postgres
```

### Redis Connection Failed

```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

Ensure Redis is running:

```bash
docker compose ps redis
docker compose logs redis
```

### Import Errors After Adding Dependencies

Restart your IDE's Python language server or run:

```bash
uv sync --locked --all-extras --dev
```
