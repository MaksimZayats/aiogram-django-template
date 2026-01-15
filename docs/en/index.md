# Modern API Template

A production-ready Django + aiogram + Celery application template with dependency injection, designed for building scalable APIs and background task processing.

## Key Features

- **Service Layer Architecture** - Clean separation between controllers and business logic
- **Dependency Injection** - Testable, loosely-coupled components using punq
- **Modern HTTP API** - Django Ninja with automatic OpenAPI documentation
- **Background Tasks** - Celery with Redis broker and typed task registry
- **Telegram Bot Ready** - aiogram integration with async controller pattern
- **Observability** - Logfire/OpenTelemetry integration for tracing and logging
- **Type Safety** - Full type hints with mypy strict mode

## Quick Links

<div class="grid cards" markdown>

-   :material-rocket-launch: **Getting Started**

    ---

    Set up your development environment and run the template in 5 minutes

    [:octicons-arrow-right-24: Quick Start](getting-started/quick-start.md)

-   :material-school: **Tutorial**

    ---

    Build a complete Todo List feature from scratch

    [:octicons-arrow-right-24: Start Tutorial](tutorial/index.md)

-   :material-lightbulb: **Concepts**

    ---

    Understand the architectural patterns used in this template

    [:octicons-arrow-right-24: Learn Concepts](concepts/index.md)

-   :material-book-open-variant: **How-To Guides**

    ---

    Step-by-step guides for common tasks

    [:octicons-arrow-right-24: Browse Guides](how-to/index.md)

</div>

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Entry Points                             │
├───────────────┬───────────────────────┬─────────────────────────┤
│   HTTP API    │     Celery Worker     │     Telegram Bot        │
│ (Django Ninja)│                       │      (aiogram)          │
├───────────────┴───────────────────────┴─────────────────────────┤
│                     Controllers (delivery/)                     │
│              HTTP Controllers │ Task Controllers                │
├─────────────────────────────────────────────────────────────────┤
│                      Services (core/)                           │
│              Business Logic │ Database Operations               │
├─────────────────────────────────────────────────────────────────┤
│                    IoC Container (ioc/)                         │
│                   Dependency Resolution                         │
├─────────────────────────────────────────────────────────────────┤
│                   Infrastructure (infrastructure/)              │
│              JWT │ Settings │ Base Classes                      │
└─────────────────────────────────────────────────────────────────┘
```

## The Golden Rule

Controllers **never** access models directly. All database operations go through services:

```
Controller → Service → Model
```

This ensures:

- **Testability** - Mock services in tests instead of patching ORM calls
- **Reusability** - Services can be shared across HTTP, Celery, and Bot controllers
- **Maintainability** - Business logic stays in one place

## Requirements

- Python 3.14+
- PostgreSQL (or SQLite for development)
- Redis (for Celery and caching)
- Docker & Docker Compose (recommended)

## Next Steps

1. **New to the template?** Start with the [Quick Start](getting-started/quick-start.md) guide
2. **Want to understand the architecture?** Read the [Concepts](concepts/index.md) section
3. **Ready to build?** Follow the [Tutorial](tutorial/index.md) to create a complete feature
