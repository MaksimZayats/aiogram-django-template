# Modern API Template

Production-ready template for building modern Python applications with **Django** and **Celery** — featuring dependency injection, type-safe configuration, and comprehensive observability.

## Features

- **HTTP API** — Django-Ninja with automatic OpenAPI documentation
- **Background Tasks** — Celery with beat scheduler
- **Dependency Injection** — punq IoC container
- **Type-Safe Config** — Pydantic Settings with validation
- **Observability** — Logfire (OpenTelemetry) integration
- **Telegram Bot** — aiogram with async handlers and commands
- **Production Ready** — Docker Compose with PgBouncer, Redis, MinIO

## Quick Start

```bash
# Clone the repository
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template

# Install dependencies
uv sync --locked --all-extras --dev

# Configure environment (includes COMPOSE_FILE for local development)
cp .env.example .env

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose up -d postgres redis minio

# Create MinIO buckets, run migrations, and collect static files
docker compose up minio-create-buckets migrations collectstatic

# Start development server
make dev
```

The API is available at `http://localhost:8000` with interactive docs at `/docs`.

## Documentation

Full documentation is available at [template.zayats.dev](https://template.zayats.dev).

- [Getting Started](https://template.zayats.dev/getting-started/)
- [Tutorials](https://template.zayats.dev/tutorials/)
- [Core Concepts](https://template.zayats.dev/concepts/)
- [Configuration](https://template.zayats.dev/configuration/)
- [Deployment](https://template.zayats.dev/deployment/)

## Project Structure

```
src/
├── core/           # Business logic and settings
├── delivery/       # HTTP API, Telegram bot, Celery tasks
├── infrastructure/ # Cross-cutting concerns (JWT, logging, etc.)
└── ioc/            # Dependency injection container
```

## Commands

```bash
make dev           # Start development server
make celery-dev    # Start Celery worker
make bot-dev       # Start Telegram bot
make format        # Format code
make lint          # Run linters
make test          # Run tests
```

## License

MIT
