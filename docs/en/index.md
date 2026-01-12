---
title: Home
summary: Django + aiogram + Celery application template
order: 1
sidebar_title: Home
---

# myproject

Django + aiogram + Celery application with **punq** dependency injection.

## Features

- **Django 6+** - Modern web framework
- **aiogram 3** - Async Telegram Bot API framework
- **Celery** - Distributed task queue
- **punq** - Lightweight dependency injection container
- **Django-Ninja** - Fast, async-ready REST API

## Quick Start

```bash
# Install dependencies
uv sync --locked --all-extras --dev

# Build base Docker image
docker compose build base

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up postgres pgbouncer minio redis -d

# Run database migrations
make migrate

# Start development server
make dev
```

## Module Structure

| Module | Description |
|--------|-------------|
| `core/` | Business logic and domain models |
| `delivery/` | External interfaces (HTTP API, Telegram bot, CLI) |
| `infrastructure/` | Cross-cutting concerns (JWT, auth, settings) |
| `ioc/` | Dependency injection container configuration |
| `tasks/` | Celery task definitions |
