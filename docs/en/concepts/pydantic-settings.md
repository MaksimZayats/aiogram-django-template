# Pydantic Settings

Configuration is managed using Pydantic's `BaseSettings`, which loads values from environment variables with type validation.

## Why Pydantic Settings?

- **Type safety** - Configuration is validated at startup
- **Environment-based** - Values come from environment variables
- **Defaults** - Sensible defaults with override capability
- **Secrets** - `SecretStr` for sensitive values
- **Computed fields** - Derive complex values from simple ones

## Basic Structure

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
```

This class:

- Loads `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- Requires `secret_key` (no default)
- Uses defaults for `algorithm` and `access_token_expire_minutes`

## Environment Variable Prefixes

Each settings class uses a prefix to avoid naming conflicts:

| Prefix | Settings Class | Example Variables |
|--------|----------------|-------------------|
| `DJANGO_` | `SecuritySettings` | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` |
| `JWT_` | `JWTSettings` | `JWT_SECRET_KEY`, `JWT_ALGORITHM` |
| `CELERY_` | `CelerySettings` | `CELERY_WORKER_PREFETCH_MULTIPLIER` |
| `TELEGRAM_BOT_` | `TelegramBotSettings` | `TELEGRAM_BOT_TOKEN` |
| `AWS_S3_` | `StorageSettings` | `AWS_S3_BUCKET_NAME` |
| None | `RedisSettings` | `REDIS_URL`, `DATABASE_URL` |

## Settings Examples

### Security Settings

```python
# src/core/configs/core.py
class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DJANGO_")

    debug: bool = False
    secret_key: SecretStr
    allowed_hosts: list[str] = ["*"]
```

### Database Settings

```python
# src/core/configs/core.py
import dj_database_url
from pydantic import computed_field


class DatabaseSettings(BaseSettings):
    default_auto_field: str = "django.db.models.BigAutoField"
    conn_max_age: int = 600
    database_url: str = "sqlite:///db.sqlite3"

    @computed_field()
    def databases(self) -> dict[str, Any]:
        return {
            "default": dj_database_url.parse(
                self.database_url,
                conn_max_age=self.conn_max_age,
            ),
        }
```

### JWT Settings

```python
# src/infrastructure/jwt/services.py
from datetime import timedelta


class JWTServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)
```

### Celery Settings

```python
# src/delivery/tasks/settings.py
from pydantic import Field


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY_")

    # Worker settings
    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int | None = 1000

    # Task execution
    task_acks_late: bool = True
    task_time_limit: int | None = 300
    task_soft_time_limit: int | None = 270

    # Serialization
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = Field(default_factory=lambda: ["json"])
```

## Secret Handling

Use `SecretStr` for sensitive values:

```python
from pydantic import SecretStr


class DatabaseSettings(BaseSettings):
    password: SecretStr


# Accessing the value
settings = DatabaseSettings()
password = settings.password.get_secret_value()  # Returns actual string

# SecretStr prevents accidental logging
print(settings.password)  # Output: **********
```

## Computed Fields

Use `@computed_field` for derived values:

```python
from pydantic import computed_field


class CacheSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CACHE_")

    default_timeout: int = 300
    redis_settings: RedisSettings = Field(default_factory=RedisSettings)

    @computed_field()
    def caches(self) -> dict[str, Any]:
        return {
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": self.redis_settings.redis_url.get_secret_value(),
                "TIMEOUT": self.default_timeout,
            },
        }
```

## Django Settings Adapter

The template uses an adapter to apply Pydantic settings to Django:

```python
# src/core/configs/django.py
from infrastructure.django.settings.pydantic_adapter import PydanticSettingsAdapter

application_settings = ApplicationSettings()
security_settings = SecuritySettings()
database_settings = DatabaseSettings()

adapter = PydanticSettingsAdapter()
adapter.adapt(
    database_settings,
    application_settings,
    security_settings,
    settings_locals=locals(),  # Updates Django settings module
)
```

This:

1. Instantiates Pydantic settings (loads from environment)
2. Adapts them to Django's expected format
3. Updates the Django settings module

## IoC Registration

Settings are registered in the IoC container:

```python
# src/ioc/registries/core.py
def _register_settings(container: Container) -> None:
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(),
        scope=Scope.singleton,
    )
```

Factory pattern is used because:

- Settings load from environment at instantiation time
- Must be created fresh (not reused from module level)
- Singleton scope ensures one instance per container

## Environment Files

### Development (`.env`)

```bash
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-change-in-production

DATABASE_URL=postgres://postgres:postgres@localhost:5432/app

REDIS_URL=redis://localhost:6379

JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

TELEGRAM_BOT_TOKEN=your-bot-token

LOGFIRE_ENABLED=false
```

### Production

```bash
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<strong-random-key>

DATABASE_URL=postgres://user:pass@prod-db:5432/app

REDIS_URL=redis://:password@prod-redis:6379

JWT_SECRET_KEY=<strong-random-key>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=<your-token>
```

## Best Practices

### 1. Always Use Prefixes

```python
# ✅ GOOD - Prefixed to avoid conflicts
class JWTSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")
    secret_key: SecretStr

# ❌ BAD - Could conflict with other settings
class JWTSettings(BaseSettings):
    secret_key: SecretStr  # Would look for SECRET_KEY
```

### 2. Require Secrets

```python
# ✅ GOOD - No default for secrets
secret_key: SecretStr  # Will fail if not provided

# ❌ BAD - Default secret
secret_key: SecretStr = SecretStr("default")  # Security risk
```

### 3. Sensible Defaults

```python
# ✅ GOOD - Safe defaults
debug: bool = False  # Secure by default
timeout: int = 30    # Reasonable default

# ❌ BAD - Unsafe defaults
debug: bool = True   # Insecure default
```

### 4. Validate Types

```python
from pydantic import EmailStr, HttpUrl, PositiveInt

class ApiSettings(BaseSettings):
    email: EmailStr           # Validates email format
    base_url: HttpUrl         # Validates URL format
    timeout: PositiveInt      # Must be positive integer
```

## Related Concepts

- [IoC Container](ioc-container.md) - How settings are registered
- [Factory Pattern](factory-pattern.md) - How settings are used
