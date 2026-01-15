# Modern API Template

Production-ready template for building modern Python applications with **Django**, **aiogram**, and **Celery** —
featuring dependency injection, type-safe configuration, and comprehensive observability.

## Features

- **HTTP API** — [Django Ninja](https://django-ninja.dev/) with automatic OpenAPI documentation
- **Background Tasks** — [Celery](https://docs.celeryq.dev/en/stable/) with beat scheduler
- **Telegram Bot** — [aiogram 3.x](https://docs.aiogram.dev/) with async handlers and commands
- **Dependency Injection** — [punq](https://github.com/bobthemighty/punq) IoC container
- **Type-Safe Config** — [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) with
  validation
- **Observability** — [Logfire](https://logfire.pydantic.dev/docs/) (OpenTelemetry) integration
- **Production Ready** — Docker Compose with PostgreSQL, PgBouncer, Redis, MinIO

## Prerequisites

Before getting started, ensure you have installed:

- **uv** — Blazingly fast Python package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker & Docker Compose** — For infrastructure
  services ([Install Docker](https://docs.docker.com/get-started/get-docker/))

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template
```

### 2. Rename the Project

Replace the default project name in `pyproject.toml` with your own.
Use lowercase letters, numbers, and hyphens (e.g., `my-awesome-api`, `backend-service`).

### 3. Install Dependencies

```bash
uv sync --locked --all-extras --dev
```

### 4. Configure Environment

```bash
cp .env.example .env
```

The `.env.example` contains sensible defaults for local development. Key variables:

- `DJANGO_SECRET_KEY` — Django secret key
- `JWT_SECRET_KEY` — JWT signing key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string

### 5. Start Infrastructure Services

```bash
docker compose up -d postgres redis minio
```

This starts:

- **PostgreSQL 18** — Primary database
- **PgBouncer** — Connection pooling (transaction mode)
- **Redis** — Cache and Celery broker
- **MinIO** — S3-compatible object storage

### 6. Initialize Database and Storage

```bash
docker compose up minio-create-buckets migrations collectstatic
```

This runs one-time setup tasks:

1. Creates MinIO buckets for static/media files
2. Applies Django database migrations
3. Collects static files to MinIO

### 7. Start Development Server

```bash
make dev
```

The API is available at `http://localhost:8000` with interactive docs at `/api/docs`.

## Verify Installation

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Documentation

Full documentation is available at [template.zayats.dev](https://template.zayats.dev).

| Section                                                                                         | Description                                |
|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| [Quick Start](https://template.zayats.dev/getting-started/quick-start/)                         | Get running in 5 minutes                   |
| [Project Structure](https://template.zayats.dev/getting-started/project-structure/)             | Understand the codebase organization       |
| [Development Environment](https://template.zayats.dev/getting-started/development-environment/) | IDE setup and tooling                      |
| [Tutorial: Build a Todo List](https://template.zayats.dev/tutorial/)                            | Learn by building a complete feature       |
| [Concepts](https://template.zayats.dev/concepts/)                                               | Service layer, IoC, controllers, factories |
| [How-To Guides](https://template.zayats.dev/how-to/)                                            | Add domains, tasks, secure endpoints       |
| [Reference](https://template.zayats.dev/reference/)                                             | Environment variables, Makefile, Docker    |

## Tech Stack

| Component       | Technology        | Documentation                                                                              |
|-----------------|-------------------|--------------------------------------------------------------------------------------------|
| Web Framework   | Django 6+         | [docs.djangoproject.com](https://docs.djangoproject.com/en/stable/)                        |
| HTTP API        | Django Ninja 1.x  | [django-ninja.dev](https://django-ninja.dev/)                                              |
| Telegram Bot    | aiogram 3.x       | [docs.aiogram.dev](https://docs.aiogram.dev/)                                              |
| Task Queue      | Celery 5.x        | [docs.celeryq.dev](https://docs.celeryq.dev/en/stable/)                                    |
| Validation      | Pydantic 2.x      | [docs.pydantic.dev](https://docs.pydantic.dev/latest/)                                     |
| Settings        | Pydantic Settings | [docs.pydantic.dev/settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| IoC Container   | punq              | [github.com/bobthemighty/punq](https://github.com/bobthemighty/punq)                       |
| Observability   | Logfire           | [Logfire docs](https://logfire.pydantic.dev/docs/)                                         |
| Package Manager | uv                | [docs.astral.sh/uv](https://docs.astral.sh/uv/)                                            |

## License

[MIT](LICENSE.md)
