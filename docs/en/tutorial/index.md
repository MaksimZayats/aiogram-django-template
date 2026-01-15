# Tutorial: Build a Todo List

In this tutorial, you'll build a complete **Todo List** feature from scratch, learning the core patterns of the Modern API Template along the way.

## What You'll Build

A fully-functional Todo List with:

- **Django model** - Store todos in the database
- **Service layer** - Business logic for CRUD operations
- **REST API** - HTTP endpoints with JWT authentication
- **Admin panel** - Django admin for managing todos
- **Background task** - Celery task to clean up old completed todos
- **Observability** - Logfire/OpenTelemetry integration
- **Tests** - Integration tests for API and Celery

## Prerequisites

Before starting this tutorial, you should:

- Have the application [running locally](../getting-started/quick-start.md)
- Understand the [project structure](../getting-started/project-structure.md)
- Be familiar with Django and Python

## Tutorial Steps

| Step | What You'll Learn |
|------|-------------------|
| [Step 1: Model & Service](01-model-and-service.md) | Create the Todo model and TodoService |
| [Step 2: IoC Registration](02-ioc-registration.md) | Register the service in the IoC container |
| [Step 3: HTTP API & Admin](03-http-api.md) | Build REST endpoints and admin panel |
| [Step 4: Celery Tasks](04-celery-tasks.md) | Create a background cleanup task |
| [Step 5: Observability](05-observability.md) | Set up Logfire for tracing |
| [Step 6: Testing](06-testing.md) | Write integration tests |

## Architecture Preview

By the end of this tutorial, you'll have created:

```
src/
├── core/
│   └── todo/
│       ├── __init__.py
│       ├── apps.py            # Django app config
│       ├── models.py          # Todo model
│       └── services.py        # TodoService
├── delivery/
│   ├── http/
│   │   └── todo/
│   │       ├── __init__.py
│   │       ├── controllers.py # TodoController
│   │       └── admin.py       # TodoAdmin
│   └── tasks/
│       └── tasks/
│           └── todo_cleanup.py # TodoCleanupTaskController
└── ioc/
    └── registries/
        ├── core.py            # + TodoService registration
        └── delivery.py        # + TodoController registration
```

## The Golden Rule

Throughout this tutorial, remember the **golden rule**:

```
Controller → Service → Model

✅ Controller imports Service
✅ Service imports Model
❌ Controller imports Model (NEVER)
```

This separation ensures your code is testable, maintainable, and follows best practices.

## Time Estimate

This tutorial takes approximately 30-45 minutes to complete if you're coding along. Feel free to skip ahead if you're just reading.

## Let's Begin!

Ready? Start with [Step 1: Model & Service](01-model-and-service.md).
