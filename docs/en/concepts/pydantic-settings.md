# Pydantic Settings

Type-safe configuration with environment variable support using [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

## Why Pydantic Settings?

- **Type Safety** — Configuration values are validated at startup
- **Environment Variables** — Automatic loading from environment
- **Defaults** — Sensible defaults with override capability
- **Documentation** — Self-documenting configuration

## Basic Pattern

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
```

This class:

- Reads from `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- Validates types automatically
- Provides defaults for `algorithm` and `access_token_expire_minutes`
- Keeps `secret_key` secure with `SecretStr`

## Environment Variable Prefixes

Each settings class has its own prefix:

| Class | Prefix | Example Variables |
|-------|--------|-------------------|
| `JWTServiceSettings` | `JWT_` | `JWT_SECRET_KEY` |
| `SecuritySettings` | `DJANGO_` | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` |
| `TelegramBotSettings` | `TELEGRAM_BOT_` | `TELEGRAM_BOT_TOKEN` |
| `AWSS3Settings` | `AWS_S3_` | `AWS_S3_ACCESS_KEY_ID` |
| `LogfireSettings` | `LOGFIRE_` | `LOGFIRE_ENABLED`, `LOGFIRE_TOKEN` |
| `LoggingConfig` | `LOGGING_` | `LOGGING_LEVEL` |

## Computed Fields

Use `@computed_field` for derived values:

```python
from datetime import timedelta
from pydantic import computed_field


class JWTServiceSettings(BaseSettings):
    access_token_expire_minutes: int = 15

    @computed_field()
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)
```

## Nested Settings

Compose settings with `Field(default_factory=...)`:

```python
from pydantic import Field


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY_")

    redis_settings: RedisSettings = Field(default_factory=RedisSettings)
```

## Secret Values

Use `SecretStr` for sensitive data:

```python
from pydantic import SecretStr


class SecuritySettings(BaseSettings):
    secret_key: SecretStr


# Usage
settings = SecuritySettings()
key = settings.secret_key.get_secret_value()  # Explicit unwrapping required
```

`SecretStr` prevents accidental logging of secrets.

## Complex Types

### Lists

```python
class HTTPSettings(BaseSettings):
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost"])
```

In `.env`:

```bash
ALLOWED_HOSTS='["example.com", "api.example.com"]'
```

### Enums

```python
from enum import StrEnum


class Environment(StrEnum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"


class ApplicationSettings(BaseSettings):
    environment: Environment = Environment.PRODUCTION
```

## IoC Container Integration

Settings are registered in the container with factory functions:

```python
def _register_services(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(),
    )

    container.register(
        JWTService,
        scope=Scope.singleton,
    )
```

The factory ensures environment variables are read during container setup.

## Django Settings Adapter

Pydantic settings are converted to Django format:

```python
# core/configs/django.py
from infrastructure.django.settings.pydantic_adapter import PydanticSettingsAdapter

application_settings = ApplicationSettings()
security_settings = SecuritySettings()

adapter = PydanticSettingsAdapter()
adapter.adapt(
    application_settings,
    security_settings,
    settings_locals=locals(),
)
```

The adapter:

1. Iterates over Pydantic model fields
2. Converts field names to UPPER_CASE
3. Unwraps `SecretStr` values
4. Adds to Django's settings namespace

See [Django Settings Adapter](../configuration/django-adapter.md) for details.

## Validation

Pydantic validates values at instantiation:

```python
class Settings(BaseSettings):
    port: int = 8000
    timeout: float = 30.0
```

```bash
# .env
PORT=invalid  # Will raise ValidationError at startup
```

This catches configuration errors early, during application startup.

## Custom Validators

```python
from pydantic import field_validator


class DatabaseSettings(BaseSettings):
    conn_max_age: int = 600

    @field_validator("conn_max_age")
    @classmethod
    def validate_conn_max_age(cls, v: int) -> int:
        if v < 0:
            raise ValueError("conn_max_age must be non-negative")
        return v
```

## Testing

Override settings in tests:

```python
import os

def test_with_custom_settings():
    os.environ["JWT_SECRET_KEY"] = "test-secret"
    settings = JWTServiceSettings()
    assert settings.algorithm == "HS256"
```

Or use `.env.test`:

```bash
# .env.test
JWT_SECRET_KEY=test-secret-key
DATABASE_URL=sqlite:///test.db
```

## Real Examples

### Database Settings

```python
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

### S3 Storage Settings

```python
class AWSS3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWS_S3_")

    endpoint_url: str
    access_key_id: str
    secret_access_key: SecretStr
    protected_bucket_name: str = "protected"
    public_bucket_name: str = "public"
```

## Related Topics

- [Environment Variables Reference](../reference/environment-variables.md) — All configuration options
- [Django Settings Adapter](../configuration/django-adapter.md) — How settings are adapted
- [Production Configuration](../configuration/production.md) — Production settings
