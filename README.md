# Modern Python API Template

A production-ready template for building Django APIs with async task processing.

Stack: Django 6+ / django-ninja / Celery / PostgreSQL / Redis

## Quick Start

```bash
# Install uv if you haven't
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url> && cd aiogram-django-template
uv sync --locked --all-extras --dev
cp .env.example .env  # edit with your values

# Start services
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up -d

# Run migrations and dev server
make migrate
make dev
```

Bot and Celery worker (separate terminals):

```bash
uv run python -m delivery.bot
make celery-dev
```

## Core Ideas

### Dependency Injection with punq

Everything goes through the IoC container. Services declare dependencies in `__init__`, container wires them up:

```python
class UserTokenController(Controller):
    def __init__(self, jwt_service: JWTService, refresh_service: RefreshSessionService):
        self._jwt = jwt_service
        self._refresh = refresh_service
```

Register in `src/ioc/container.py`, resolve anywhere. This makes testing trivial - just swap registrations.

### Controller Pattern

HTTP endpoints and Celery tasks use the same pattern. Extend `Controller`, implement `register()`:

```python
class MyController(Controller):
    def register(self, registry: Router) -> None:
        registry.add_api_operation("/endpoint", ["POST"], self.my_method)
```

Controllers auto-wrap methods with exception handling. Override `handle_exception()` for custom error responses.

### Testing with IoC Overrides

Each test gets a fresh container. Need to mock something? Override before creating the test client:

```python
def test_something(container: Container):
    container.register(MyService, instance=mock_service)
    client = TestClientFactory(NinjaAPIFactory(container))()
    # requests now use mock_service
```

See `tests/integration/` for examples.

## Project Structure

```
src/
├── core/           # Business logic, models
├── delivery/       # HTTP API, Telegram bot
│   ├── http/       # django-ninja endpoints
│   └── bot/        # aiogram handlers
├── infrastructure/ # JWT, auth, base classes
├── ioc/            # Container setup
└── tasks/          # Celery tasks
```

## Commands

| Command           | What it does                      |
|-------------------|-----------------------------------|
| `make dev`        | Run Django dev server             |
| `make celery-dev` | Run Celery worker                 |
| `make migrate`    | Apply migrations                  |
| `make format`     | Format code (ruff)                |
| `make lint`       | Run all linters                   |
| `make test`       | Run tests (80% coverage required) |

## Environment Variables

Key variables (see `.env.example` for full list):

- `DJANGO_SECRET_KEY` - Django secret
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis for Celery broker/backend
- `TELEGRAM_BOT_TOKEN` - Bot token from @BotFather

## Docker

For production-like setup:

```bash
docker compose up -d
```

Services: `api` (gunicorn), `celery`, `bot`, `postgres`, `pgbouncer`, `redis`, `minio`

## License

[MIT](LICENSE.md) © Maksim Zayats
