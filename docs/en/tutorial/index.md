# Tutorial: Build a Todo List

This hands-on tutorial guides you through building a complete **Todo List** feature using the Modern Django API Template. You will learn the core architectural patterns while creating a real, working feature.

## What You'll Build

By the end of this tutorial, you will have built:

- **Todo Model** - A Django model to store todo items with user ownership
- **TodoService** - A service layer encapsulating all database operations
- **HTTP API** - RESTful endpoints for CRUD operations using Django Ninja
- **Celery Task** - A background task to clean up completed todos
- **Admin Interface** - Django admin for managing todos
- **Tests** - Integration tests with IoC override capability

## Architecture Overview

The feature follows the template's layered architecture:

```
HTTP Request
     |
     v
+-----------------+
|   Controller    |  <-- Handles HTTP, validation, auth
+-----------------+
     |
     v
+-----------------+
|    Service      |  <-- Business logic, domain rules
+-----------------+
     |
     v
+-----------------+
|     Model       |  <-- Data persistence (Django ORM)
+-----------------+
```

This separation ensures:

- **Testability** - Each layer can be tested in isolation
- **Maintainability** - Business logic stays independent of delivery mechanism
- **Flexibility** - The same service works for HTTP, Celery, and Telegram bot

## Prerequisites

Before starting this tutorial, make sure you have:

- [x] Completed the [Quick Start](../getting-started/quick-start.md) guide
- [x] Development environment running (PostgreSQL, Redis)
- [x] Understanding of Python type hints and Pydantic

## Tutorial Steps

| Step | Title | What You'll Learn |
|------|-------|-------------------|
| [Step 1](01-model-and-service.md) | Model & Service | Django models, service layer pattern, domain exceptions |
| [Step 2](02-ioc-registration.md) | IoC Registration | Dependency injection with punq, container configuration |
| [Step 3](03-http-api.md) | HTTP API & Admin | Controllers, Pydantic schemas, rate limiting, admin |
| [Step 4](04-celery-tasks.md) | Celery Tasks | Task controllers, background jobs, task registry |
| [Step 5](05-observability.md) | Observability | Structured logging, metrics, health checks |
| [Step 6](06-testing.md) | Testing | Integration tests, IoC overrides, test factories |

## Getting Help

If you encounter issues:

1. Check that all services are running: `docker compose ps`
2. Review logs: `docker compose logs -f`
3. Ensure environment variables are set correctly in `.env`

Let's get started with [Step 1: Model & Service](01-model-and-service.md)!
