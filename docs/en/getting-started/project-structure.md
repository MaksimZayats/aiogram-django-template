# Project Structure

Understanding the directory layout and module organization.

## Directory Tree

```
.
├── src/                          # Application source code
│   ├── core/                     # Business logic and domain
│   │   ├── configs/              # Application configuration
│   │   │   ├── core.py           # Core settings (database, app, security)
│   │   │   ├── django.py         # Django settings module
│   │   │   └── infrastructure.py # Bootstrap function
│   │   └── user/                 # User domain module
│   │       ├── models.py         # Django models
│   │       └── services.py       # Business logic
│   │
│   ├── delivery/                 # External interfaces
│   │   ├── http/                 # HTTP API (Django-Ninja)
│   │   │   ├── api.py            # API instance
│   │   │   ├── factories.py      # NinjaAPI factory
│   │   │   ├── user/             # User endpoints
│   │   │   │   └── controllers.py
│   │   │   └── health/           # Health check endpoint
│   │   │       └── controllers.py
│   │   │
│   │   ├── bot/                  # Telegram bot (aiogram)
│   │   │   ├── __main__.py       # Bot entry point
│   │   │   ├── controllers/      # Bot controllers (AsyncController)
│   │   │   │   └── commands.py   # Command handlers
│   │   │   ├── factories.py      # Bot & Dispatcher factories
│   │   │   └── settings.py       # Bot settings
│   │   │
│   │   └── tasks/                # Celery tasks
│   │       ├── app.py            # Celery app instance
│   │       ├── factories.py      # App & Registry factories
│   │       ├── registry.py       # Task registry
│   │       └── tasks/            # Task controllers
│   │           └── ping.py
│   │
│   ├── infrastructure/           # Cross-cutting concerns
│   │   ├── delivery/             # Controller base classes
│   │   │   └── controllers.py    # Controller ABC
│   │   ├── django/               # Django integration
│   │   │   ├── auth.py           # JWT authentication
│   │   │   ├── settings/         # Settings adapter
│   │   │   └── refresh_sessions/ # Refresh token management
│   │   ├── jwt/                  # JWT service
│   │   │   └── services.py
│   │   ├── logging/              # Logging configuration
│   │   │   └── configuration.py
│   │   └── otel/                 # OpenTelemetry/Logfire
│   │       └── logfire.py
│   │
│   └── ioc/                      # Dependency injection
│       └── container.py          # punq container configuration
│
├── tests/                        # Test suite
│   ├── conftest.py               # Global fixtures
│   └── integration/              # Integration tests
│       ├── conftest.py           # Integration fixtures
│       └── factories.py          # Test factories
│
├── docs/                         # Documentation (MkDocs)
│   ├── mkdocs.yml                # MkDocs configuration
│   └── en/                       # English documentation
│
├── docker-compose.yaml           # Production Docker Compose
├── docker-compose.local.yaml     # Local development overrides
├── Dockerfile                    # Application container
├── Makefile                      # Development commands
├── pyproject.toml                # Project metadata & dependencies
└── manage.py                     # Django management script
```

## Module Responsibilities

### `core/` — Business Logic and Services

Contains domain models, services, and application settings. **Services are the only way to access models from the delivery layer.**

```
core/
├── configs/           # Application settings
│   └── core.py        # ApplicationSettings, DatabaseSettings
├── user/
│   ├── models.py      # Django ORM models
│   └── services.py    # UserService (business logic + ORM access)
└── health/
    └── services.py    # HealthService
```

**Key principle**: All database operations are encapsulated in services. Controllers never import models directly.

```python
# core/user/services.py
class UserService:
    def get_user_by_id(self, user_id: int) -> User:
        return User.objects.get(id=user_id)

    def create_user(self, username: str, email: str, password: str) -> User:
        return User.objects.create_user(username=username, email=email, password=password)
```

### `delivery/` — External Interfaces

Handles communication with the outside world. **Controllers use services, never models directly.**

- **`http/`** — REST API endpoints using Django-Ninja
- **`bot/`** — Telegram bot commands and handlers
- **`tasks/`** — Celery background tasks

```python
# delivery/http/user/controllers.py
class UserController(Controller):
    def __init__(self, user_service: UserService) -> None:  # ✅ Inject service
        self._user_service = user_service

    def get_user(self, request: HttpRequest, user_id: int) -> UserSchema:
        user = self._user_service.get_user_by_id(user_id)  # ✅ Use service
        return UserSchema.model_validate(user, from_attributes=True)
```

Each delivery mechanism has its own entry point but shares the same IoC container.

### `infrastructure/` — Cross-Cutting Concerns

Technical capabilities shared across the application:

- **`controllers.py`** — Base controller classes (`Controller` for sync, `AsyncController` for async handlers)
- **`jwt/`** — JWT token issuance and validation
- **`django/auth.py`** — HTTP Bearer authentication
- **`logging/`** — Colored console logging
- **`otel/`** — OpenTelemetry instrumentation

### `ioc/` — Dependency Injection

The IoC container configuration in `container.py`:

```python
def get_container() -> Container:
    container = Container()
    _register_services(container)
    _register_http(container)
    _register_controllers(container)
    _register_celery(container)
    _register_bot(container)
    return container
```

## Entry Points

### HTTP API

```
manage.py runserver
    └── delivery/http/app.py (configure_infrastructure + WSGI)
        └── delivery/http/api.py
            └── ioc/container.py (get_container + resolve NinjaAPI)
```

### Telegram Bot

```
python -m delivery.bot
    └── delivery/bot/__main__.py
        └── ioc/container.py
```

### Celery Worker

```
celery -A delivery.tasks.app worker
    └── delivery/tasks/app.py
        └── ioc/container.py
```

## Configuration Flow

```
Environment Variables (.env)
         │
         ▼
Pydantic Settings Classes (core/configs/)
         │
         ▼
PydanticSettingsAdapter (infrastructure/django/settings/)
         │
         ▼
Django Settings (core/configs/django.py)
```

The adapter converts Pydantic settings to Django's expected format, providing type safety and validation.

## Testing Structure

```
tests/
├── conftest.py              # Shared fixtures, pytest configuration
└── integration/
    ├── conftest.py          # Integration-specific fixtures
    ├── factories.py         # Test factories (NinjaAPI, TestClient, etc.)
    └── http/
        └── test_user.py     # HTTP endpoint tests
```

Test factories enable per-test IoC container isolation, allowing you to mock dependencies for specific tests.

## Next Steps

- [Service Layer Architecture](../concepts/service-layer.md) — How controllers interact with business logic
- [IoC Container](../concepts/ioc-container.md) — Deep dive into dependency injection
- [Controller Pattern](../concepts/controller-pattern.md) — Understand the controller abstraction
- [Your First API Endpoint](../tutorials/first-api-endpoint.md) — Add a new endpoint
