# Project Structure

Understanding the codebase organization is essential for effective development. This template follows a layered architecture that separates concerns and promotes maintainability.

## High-Level Overview

```
fastdjango/
├── src/                    # Application source code
│   ├── core/               # Business logic and domain models
│   ├── delivery/           # External interfaces (HTTP, Celery)
│   ├── infrastructure/     # Cross-cutting concerns
│   └── ioc/                # Dependency injection container
├── tests/                  # Test suite
├── docs/                   # Documentation (MkDocs)
├── docker-compose.yaml     # Production Docker services
├── docker-compose.local.yaml # Development overrides
├── Makefile                # Development commands
└── pyproject.toml          # Project configuration
```

## The `src/` Directory

All application code lives under `src/`. This is structured as a Python namespace package with four main modules.

### `configs/` - Application Configuration

The configs module contains all application configuration and Pydantic settings classes.

```
src/configs/
├── core.py             # Core settings (environment, application settings)
├── django.py           # Django settings module
├── infrastructure.py   # Infrastructure settings (S3, Redis)
└── logging.py          # Logging configuration
```

### `core/` - Business Logic

The core module contains your domain models, business rules, and services. This is where the heart of your application logic resides.

```
src/core/
├── health/                 # Health check domain
│   └── services.py         # Health check service
├── user/                   # User domain
│   ├── models.py           # User and RefreshSession models
│   ├── services/           # User domain services
│   │   ├── user.py         # User business logic
│   │   └── refresh_session.py  # Refresh token management
│   └── migrations/         # Database migrations
└── exceptions.py           # Base domain exceptions
```

!!! important "The Golden Rule"
    Services in `core/` are the **only** place where you should access Django models directly. Controllers in `delivery/` must always go through services.

### `delivery/` - External Interfaces

The delivery module handles all external communication. Each sub-module is a separate entry point into your application.

```
src/delivery/
├── http/                   # HTTP API (FastAPI)
│   ├── app.py              # WSGI application factory
│   ├── factories.py        # FastAPI factory
│   ├── auth/               # Authentication components
│   │   └── jwt.py          # JWT auth for FastAPI
│   ├── health/             # Health check endpoints
│   │   └── controllers.py
│   └── user/               # User endpoints
│       └── controllers.py
├── services/               # Delivery-specific services
│   └── jwt.py              # JWT token service
└── tasks/                  # Celery background tasks
    ├── app.py              # Celery application factory
    ├── registry.py         # Task name registry
    ├── factories.py        # Celery factory
    └── tasks/              # Task controllers
        └── ping.py
```

#### HTTP Controllers

HTTP controllers define API endpoints using FastAPI's routing:

```python
# src/delivery/http/user/controllers.py
from dataclasses import dataclass, field
from fastapi import APIRouter, Depends
from delivery.http.auth.jwt import JWTAuth, JWTAuthFactory

@dataclass
class UserController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _user_service: UserService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/users/me",
            endpoint=self.get_current_user,
            methods=["GET"],
            dependencies=[Depends(self._jwt_auth)],
            response_model=UserSchema,
        )
```

#### Celery Task Controllers

Task controllers follow the same pattern but register with Celery:

```python
# src/delivery/tasks/tasks/ping.py
class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> str:
        return "pong"
```

### `infrastructure/` - Cross-Cutting Concerns

Infrastructure code supports the application but is not domain-specific.

```
src/infrastructure/
├── anyio/                  # AnyIO configuration
│   └── configurator.py     # Thread pool configuration
├── celery/                 # Celery utilities
│   └── registry.py         # Base task registry
├── delivery/               # Controller base classes
│   ├── controllers.py      # Controller base class
│   └── request.py          # Request info service
├── django/                 # Django extensions
│   ├── configurator.py     # Django setup
│   └── settings/           # Settings adapters
│       └── pydantic_adapter.py
├── punq/                   # IoC container extension
│   └── container.py        # AutoRegisteringContainer
├── telemetry/              # OpenTelemetry/Logfire integration
│   ├── configurator.py     # Logfire configuration
│   └── instrumentor.py     # Library instrumentation
└── settings/               # Settings type definitions
    └── types.py
```

### `ioc/` - Dependency Injection

The IoC container wires everything together.

```
src/ioc/
├── container.py            # Container factory
└── registries/             # Component registrations
    ├── core.py             # Core services
    ├── delivery.py         # Controllers
    └── infrastructure.py   # Infrastructure services
```

The container is configured in three stages:

```python
# src/ioc/container.py
def get_container() -> Container:
    container = Container()
    register_core(container)           # Domain services
    register_infrastructure(container) # JWT, auth, etc.
    register_delivery(container)       # HTTP and Celery controllers
    return container
```

## Data Flow

Understanding how data flows through the layers:

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  delivery/http/                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Controller                                       │  │
│  │  - Validates request (Pydantic schemas)           │  │
│  │  - Calls service methods                          │  │
│  │  - Returns response (Pydantic schemas)            │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  core/                                                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Service                                          │  │
│  │  - Implements business logic                      │  │
│  │  - Accesses models via Django ORM                 │  │
│  │  - Raises domain exceptions                       │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Database (PostgreSQL)                                  │
└─────────────────────────────────────────────────────────┘
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python project configuration, dependencies, tool settings |
| `Makefile` | Development command shortcuts |
| `docker-compose.yaml` | Production Docker services |
| `docker-compose.local.yaml` | Development Docker overrides |
| `.env.example` | Template for environment variables |
| `.pre-commit-config.yaml` | Pre-commit hook configuration |

## Tests Directory

```
tests/
├── conftest.py             # Pytest fixtures
├── integration/            # Integration tests
│   ├── factories.py        # Test factories
│   ├── http/               # HTTP API tests
│   └── tasks/              # Celery task tests
└── unit/                   # Unit tests
```

## Next Steps

Now that you understand the project structure:

- **[Development Environment](development-environment.md)** - Set up your IDE
- **[Service Layer](../concepts/service-layer.md)** - Deep dive into the service pattern
- **[IoC Container](../concepts/ioc-container.md)** - Learn about dependency injection
