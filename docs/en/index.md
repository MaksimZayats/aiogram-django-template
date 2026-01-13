# Django + aiogram + Celery Template

A production-ready template for building modern Python applications with **Django**, **aiogram**, and **Celery** — featuring dependency injection, type-safe configuration, and comprehensive observability.

## Why This Template?

Building production applications requires more than just framework boilerplate. This template provides:

- **Clean Architecture** — Separation of concerns with IoC container (punq) for dependency injection
- **Type Safety** — Pydantic settings with environment variable validation
- **Multiple Interfaces** — HTTP API (Django-Ninja), Telegram bot (aiogram), background tasks (Celery)
- **Production Ready** — Docker Compose deployment, connection pooling (PgBouncer), object storage (MinIO)
- **Observable** — Logfire/OpenTelemetry integration with automatic instrumentation
- **Testable** — Test factories with per-test IoC container isolation

## Quick Links

<div class="grid cards" markdown>

-   **Getting Started**

    ---

    Set up your development environment in 5 minutes

    [:octicons-arrow-right-24: Quick Start](getting-started/quick-start.md)

-   **Tutorials**

    ---

    Step-by-step guides for common tasks

    [:octicons-arrow-right-24: Your First API Endpoint](tutorials/first-api-endpoint.md)

-   **Core Concepts**

    ---

    Understand the architectural patterns

    [:octicons-arrow-right-24: IoC Container](concepts/ioc-container.md)

-   **Deployment**

    ---

    Deploy to production with Docker Compose

    [:octicons-arrow-right-24: Docker Compose](deployment/docker-compose.md)

</div>

## Features at a Glance

| Feature | Technology | Description |
|---------|------------|-------------|
| HTTP API | Django-Ninja | Fast, type-safe REST API with automatic OpenAPI docs |
| Telegram Bot | aiogram | Async bot framework with handlers and commands |
| Background Tasks | Celery | Distributed task queue with beat scheduler |
| Dependency Injection | punq | Lightweight IoC container with automatic resolution |
| Configuration | Pydantic Settings | Type-safe config with environment variable support |
| Database | PostgreSQL + PgBouncer | Connection pooling for high concurrency |
| Object Storage | MinIO (S3-compatible) | Static files and media storage |
| Observability | Logfire | OpenTelemetry-based tracing and logging |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Entry Points                           │
├─────────────────┬─────────────────┬────────────────────────┤
│   HTTP API      │  Telegram Bot   │    Celery Worker       │
│  (Django-Ninja) │   (aiogram)     │                        │
└────────┬────────┴────────┬────────┴───────────┬────────────┘
         │                 │                    │
         └─────────────────┼────────────────────┘
                           │
                    ┌──────▼──────┐
                    │     IoC     │
                    │  Container  │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ Services│      │ Settings│      │ Infra   │
    │ (core/) │      │(Pydantic)│     │(logging)│
    └─────────┘      └─────────┘      └─────────┘
```

All entry points share the same IoC container, ensuring consistent dependency resolution across HTTP, bot, and background task contexts.

## Getting Help

- **Documentation** — You're reading it!
- **Issues** — [GitHub Issues](https://github.com/MaksimZayats/modern-django-template/issues)
- **Discussions** — [GitHub Discussions](https://github.com/MaksimZayats/modern-django-template/discussions)
