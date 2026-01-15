# Project Structure

Understanding the directory layout and module organization.

## Directory Overview

```
modern-django-template/
├── src/                          # Application source code
│   ├── core/                     # Business logic & models
│   ├── delivery/                 # External interfaces
│   ├── infrastructure/           # Cross-cutting concerns
│   ├── ioc/                      # Dependency injection
│   └── manage.py                 # Django entry point
├── tests/                        # Test suite
├── docs/                         # Documentation
├── docker-compose.yml            # Container orchestration
├── Makefile                      # Development commands
└── pyproject.toml                # Project configuration
```

## Source Code (`src/`)

### `core/` - Business Logic

Contains domain models, services, and business rules. **This is where your application logic lives.**

```
core/
├── configs/                      # Application & Django settings
│   ├── core.py                   # Pydantic settings classes
│   └── django.py                 # Django settings adapter
├── exceptions.py                 # Base application exception
├── health/                       # Health check domain
│   ├── services.py               # HealthService
│   └── apps.py                   # Django app config
└── user/                         # User domain
    ├── models.py                 # User, RefreshSession models
    ├── services.py               # UserService
    └── apps.py                   # Django app config
```

**Key principles:**

- Each domain has its own directory (`health/`, `user/`)
- Services encapsulate all database operations
- Models are Django ORM models
- Controllers never import from `core/*/models.py` directly

### `delivery/` - External Interfaces

Contains all entry points to the application: HTTP API, Celery tasks, and Telegram bot.

```
delivery/
├── http/                         # Django Ninja API
│   ├── api.py                    # NinjaAPI instance
│   ├── factories.py              # NinjaAPIFactory, AdminSiteFactory
│   ├── settings.py               # HTTP-specific settings
│   ├── health/
│   │   └── controllers.py        # HealthController
│   └── user/
│       ├── controllers.py        # UserController, UserTokenController
│       └── admin.py              # UserAdmin
├── tasks/                        # Celery workers
│   ├── app.py                    # Celery app instance
│   ├── factories.py              # CeleryAppFactory
│   ├── registry.py               # TasksRegistry, TaskName enum
│   ├── settings.py               # Celery settings
│   └── tasks/
│       └── ping.py               # PingTaskController
└── bot/                          # Telegram bot
    ├── __main__.py               # Bot entry point
    ├── factories.py              # BotFactory, DispatcherFactory
    ├── settings.py               # Bot settings
    └── controllers/
        └── commands.py           # CommandsController
```

**Key principles:**

- Controllers are the only classes that handle requests
- Controllers inject services via constructor
- Each controller has a `register()` method for route/task registration

### `infrastructure/` - Cross-Cutting Concerns

Contains shared utilities, base classes, and framework integrations.

```
infrastructure/
├── delivery/
│   └── controllers.py            # Controller, AsyncController base classes
├── django/
│   ├── auth.py                   # JWTAuth, AuthenticatedHttpRequest
│   ├── settings/
│   │   └── pydantic_adapter.py   # Django settings adapter
│   └── refresh_sessions/
│       └── models.py             # BaseRefreshSession
├── jwt/
│   └── services.py               # JWTService, JWTServiceSettings
├── celery/
│   └── registry.py               # BaseTasksRegistry
├── logging/
│   └── configuration.py          # Logging setup
└── settings/
    └── types.py                  # Environment enum
```

### `ioc/` - Dependency Injection

Contains the IoC container configuration using punq.

```
ioc/
├── container.py                  # get_container() function
└── registries/
    ├── core.py                   # Service registrations
    ├── delivery.py               # Controller registrations
    └── infrastructure.py         # Infrastructure registrations
```

**Registration order matters:**

1. `core.py` - Settings, models, services
2. `infrastructure.py` - JWT, auth, base classes
3. `delivery.py` - Controllers, factories, API instances

## Tests (`tests/`)

```
tests/
├── conftest.py                   # Shared fixtures
├── integration/
│   ├── conftest.py               # Integration test fixtures
│   ├── factories.py              # Test factories
│   ├── http/
│   │   └── test_v1_users.py      # HTTP API tests
│   └── tasks/
│       └── test_ping.py          # Celery task tests
└── unit/                         # Unit tests (if any)
```

**Key patterns:**

- `factories.py` contains `TestClientFactory`, `TestUserFactory`, etc.
- Each test gets a fresh IoC container (function-scoped)
- Use `@pytest.mark.django_db(transaction=True)` for database tests

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configs |
| `Makefile` | Development commands (`make dev`, `make test`) |
| `docker-compose.yml` | Container services |
| `.env.example` | Example environment variables |
| `CLAUDE.md` | AI assistant instructions |

## Entry Points

The application has three main entry points:

| Entry Point | Command | Description |
|------------|---------|-------------|
| HTTP API | `make dev` | Django development server |
| Celery Worker | `make celery-dev` | Background task processor |
| Telegram Bot | `uv run python -m delivery.bot` | Bot polling |

All entry points share the same IoC container, ensuring consistent dependency resolution.

## Next Steps

- [Development Environment](development-environment.md) - Set up your IDE
- [Tutorial](../tutorial/index.md) - Build a feature from scratch
- [Service Layer](../concepts/service-layer.md) - Deep dive into the architecture
