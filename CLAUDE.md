# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
uv sync --locked --all-extras --dev

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up -d

# Run development server
make dev

# Run Celery worker
make celery-dev

# Database migrations
make makemigrations
make migrate

# Code quality
make format    # ruff format + fix
make lint      # ruff, ty, pyrefly, mypy
make test      # pytest with 80% coverage requirement
```

## Architecture Overview

This is a Django + aiogram + Celery application using **punq** for dependency injection.

### Module Structure

- **`core/`** - Business logic and domain models. All services are class-based with explicit dependencies resolved via IoC container.
- **`delivery/`** - External interfaces (HTTP API, Telegram bot, CLI). Handles communication with the outside world.
- **`infrastructure/`** - Cross-cutting concerns (JWT, auth, settings adapters, controller base classes).
- **`ioc/`** - Dependency injection container configuration.
- **`tasks/`** - Celery task definitions using controller pattern.

### Entry Points

1. **HTTP API**: `manage.py` → `delivery/http/api.py` (Django-Ninja)
2. **Telegram Bot**: `delivery/bot/__main__.py` (aiogram polling)
3. **Celery Worker**: `tasks/app.py`

All entry points share the same IoC container for consistent dependency resolution.

## IoC Container Pattern

The container is configured in `src/ioc/container.py`:

```python
def get_container() -> Container:
    container = Container()
    _register_services(container)      # JWTService, RefreshSessionService
    _register_auth(container)          # JWTAuth
    _register_controllers(container)   # HTTP controllers
    _register_celery(container)        # Task controllers
    return container
```

### Registering Components

```python
# Type-based (auto-resolves dependencies from __init__ signature)
container.register(UserController, scope=Scope.singleton)

# Factory-based (for settings that load from env)
container.register(JWTServiceSettings, factory=lambda: JWTServiceSettings())

# Instance (for concrete implementations of abstract types)
container.register(type[BaseRefreshSession], instance=RefreshSession)
```

### Resolving Dependencies

```python
controller = container.resolve(UserController)
```

## Controller Pattern

All controllers extend `infrastructure/delivery/controllers.py:Controller`:

```python
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None: ...

    def handle_exception(self, exception: Exception) -> NoReturn:
        raise exception  # Override for custom error handling
```

Controllers auto-wrap all public methods with exception handling. Override `handle_exception()` to customize error responses.

### HTTP Controller Registration

```python
class UserController(Controller):
    def __init__(self, jwt_auth: JWTAuth) -> None:
        self._jwt_auth = jwt_auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation("/v1/users/me", ["GET"], self.get_me, auth=self._jwt_auth)
```

### Celery Task Controller Registration

```python
class PingTaskController(Controller):
    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)
```

## Testing Architecture

### Test Factories

Test factories in `tests/integration/factories.py` enable isolated testing with IoC override capability:

- **`NinjaAPIFactory`** - Creates API instances with unique URL namespaces per test
- **`TestClientFactory`** - Wraps API factory to create test clients
- **`UserFactory`** - Creates test users
- **`CeleryAppFactory`** - Creates Celery apps with container
- **`CeleryWorkerFactory`** - Manages test worker lifecycle

### Per-Test Container Isolation

Each test gets a fresh container (function-scoped fixtures), enabling IoC overrides:

```python
@pytest.fixture(scope="function")
def container() -> Container:
    return get_container()

@pytest.fixture(scope="function")
def test_client_factory(api_factory: NinjaAPIFactory) -> TestClientFactory:
    # New API + test client per test function for IoC override capability
    return TestClientFactory(api_factory=api_factory)
```

### Overriding IoC Registrations in Tests

To mock a component for a specific test:

```python
def test_with_mock_service(container: Container) -> None:
    # Override before creating factories
    mock_service = MagicMock()
    container.register(JWTService, instance=mock_service)

    api_factory = NinjaAPIFactory(container=container)
    test_client = TestClientFactory(api_factory=api_factory)()
    # Now all requests use mock_service
```

### HTTP API Tests

```python
@pytest.mark.django_db(transaction=True)
def test_create_user(test_client_factory: TestClientFactory) -> None:
    test_client = test_client_factory()
    response = test_client.post("/v1/users/", json={...})
```

### Celery Task Tests

```python
def test_ping_task(celery_worker_factory: CeleryWorkerFactory, container: Container) -> None:
    registry = container.resolve(TasksRegistry)
    with celery_worker_factory():  # Starts worker in context
        result = registry.ping.delay().get(timeout=1)
```

## API Factory Customization

`get_ninja_api()` and `get_celery_app()` accept optional `container` parameter for test customization:

```python
def get_ninja_api(
    container: Container | None = None,  # Custom container for tests
    urls_namespace: str | None = None,   # Unique namespace per test
) -> NinjaAPI:
```

## Configuration

Uses Pydantic BaseSettings with environment variable prefixes:
- `DJANGO_` - Django settings (SECRET_KEY, DEBUG)
- `JWT_` - JWT configuration (SECRET_KEY, algorithm, expiry)
- `AWS_S3_` - S3/MinIO storage
- `TELEGRAM_BOT_` - Bot token
- `CELERY_` - Celery settings

Settings classes are registered in IoC and injected into services.

## Test Environment

Tests use `.env.test` file loaded in `tests/conftest.py`. Required services:
- PostgreSQL (or SQLite for unit tests)
- Redis (for Celery tests)
