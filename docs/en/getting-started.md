---
title: Getting Started
summary: Installation and setup guide
order: 2
sidebar_title: Getting Started
---

# Getting Started

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- Docker & Docker Compose

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template

# Install all dependencies
uv sync --locked --all-extras --dev
```

## Infrastructure

Start the required services using Docker Compose:

!!! note
    Build the base Docker image first before running the services:
    ```bash
    docker compose -f docker-compose.yaml -f docker-compose.local.yaml build
    ```

```bash
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up -d
```

This starts:

- **PostgreSQL** - Primary database
- **Redis** - Cache and Celery broker
- **MinIO** - S3-compatible object storage

## Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DJANGO_DEBUG` | Enable debug mode |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `JWT_SECRET_KEY` | JWT signing key |

## Development Commands

```bash
# Run development server
make dev

# Run Celery worker
make celery-dev

# Database migrations
make makemigrations
make migrate

# Code quality
make format    # Format code with ruff
make lint      # Run all linters
make test      # Run tests with coverage
```

## Entry Points

The application has three entry points:

1. **HTTP API**: `make dev` - Django-Ninja REST API
2. **Telegram Bot**: `uv run python -m delivery.bot` - aiogram polling
3. **Celery Worker**: `make celery-dev` - Background tasks
