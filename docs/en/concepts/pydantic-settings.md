# Pydantic Settings

This template uses Pydantic's `BaseSettings` for configuration management. Settings classes automatically load values from environment variables, provide type validation, and integrate with the IoC container for dependency injection.

## How BaseSettings Works

Pydantic `BaseSettings` automatically loads field values from environment variables:

```python
from pydantic_settings import BaseSettings

class JWTServiceSettings(BaseSettings):
    secret_key: str      # Loaded from JWT_SECRET_KEY
    algorithm: str = "HS256"  # Default if not in env
```

When instantiated, the settings class:

1. Looks for environment variables matching field names
2. Applies any prefix defined in `model_config`
3. Validates and converts values to the declared types
4. Uses defaults for missing optional fields

## Environment Variable Prefixes

Each settings class uses a prefix to namespace its environment variables:

| Settings Class | Prefix | Example Variable |
|----------------|--------|------------------|
| `SecuritySettings` | `DJANGO_` | `DJANGO_SECRET_KEY` |
| `JWTServiceSettings` | `JWT_` | `JWT_SECRET_KEY` |
| `AWSS3Settings` | `AWS_S3_` | `AWS_S3_ENDPOINT_URL` |
| `CelerySettings` | `CELERY_` | `CELERY_TASK_TIME_LIMIT` |
| `CacheSettings` | `CACHE_` | `CACHE_DEFAULT_TIMEOUT` |

Configure the prefix using `SettingsConfigDict`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
```

## SecretStr for Sensitive Values

Use `SecretStr` for passwords, tokens, and other sensitive data:

```python
from pydantic import SecretStr


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DJANGO_")

    debug: bool = False
    secret_key: SecretStr  # Never accidentally logged or printed
```

`SecretStr` provides:

- **Masked repr**: `SecretStr('**********')` instead of actual value
- **Explicit access**: Must call `.get_secret_value()` to get the actual string
- **Accidental exposure prevention**: Won't appear in logs or stack traces

```python
settings = SecuritySettings()

# Accessing the value
print(settings.secret_key)  # SecretStr('**********')
print(settings.secret_key.get_secret_value())  # actual-secret-value
```

## Computed Properties

Use `@computed_field` for values derived from other settings:

```python
from pydantic import computed_field


class JWTServiceSettings(BaseSettings):
    access_token_expire_minutes: int = 15

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)
```

For complex computed values that should be part of the model:

```python
from pydantic import computed_field


class DatabaseSettings(BaseSettings):
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

## Real-World Examples

### JWT Service Settings

```python
from datetime import timedelta

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)
```

Environment variables:

```bash
JWT_SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
```

### Celery Settings

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY_")

    # Worker settings
    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int | None = 1000

    # Task execution
    task_acks_late: bool = True
    task_reject_on_worker_lost: bool = True
    task_time_limit: int | None = 300
    task_soft_time_limit: int | None = 270

    # Serialization
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: list[str] = Field(default_factory=lambda: ["json"])
```

### AWS S3 Settings

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWSS3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWS_S3_")

    endpoint_url: str
    access_key_id: str
    secret_access_key: SecretStr
    protected_bucket_name: str = "protected"
    public_bucket_name: str = "public"
```

Environment variables:

```bash
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=minioadmin
AWS_S3_SECRET_ACCESS_KEY=minioadmin
AWS_S3_PROTECTED_BUCKET_NAME=protected
AWS_S3_PUBLIC_BUCKET_NAME=public
```

## Registration in IoC Container

Settings are registered as singletons using factory-based registration:

```python
# ioc/registries/core.py
from punq import Container, Scope


def _register_settings(container: Container) -> None:
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )

    container.register(
        RedisSettings,
        factory=lambda: RedisSettings(),
        scope=Scope.singleton,
    )
```

```python
# ioc/registries/infrastructure.py
def _register_jwt(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(),
    )
```

!!! note "Why Factory Registration?"
    Settings use factory registration (`factory=lambda: Settings()`) rather than type-based registration because:

    1. Settings load from environment at instantiation time
    2. The factory ensures settings are created when first resolved
    3. Type-based registration would try to auto-resolve dependencies that don't exist

## Using Settings in Services

Services receive settings through dependency injection:

```python
class JWTService:
    def __init__(self, settings: JWTServiceSettings) -> None:
        self._settings = settings

    def issue_access_token(self, user_id: Any) -> str:
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(tz=UTC) + self._settings.access_token_expire,
        }

        return jwt.encode(
            payload=payload,
            key=self._settings.secret_key.get_secret_value(),
            algorithm=self._settings.algorithm,
        )
```

## Nested Settings

Settings can contain other settings classes:

```python
class StorageSettings(BaseSettings):
    static_url: str = "static/"
    media_url: str = "media/"

    s3_settings: AWSS3Settings = Field(default_factory=AWSS3Settings)

    @computed_field()
    def storages(self) -> dict[str, Any]:
        return {
            "default": {
                "BACKEND": "storages.backends.s3.S3Storage",
                "OPTIONS": {
                    "bucket_name": self.s3_settings.protected_bucket_name,
                    "access_key": self.s3_settings.access_key_id,
                    "secret_key": self.s3_settings.secret_access_key.get_secret_value(),
                    "endpoint_url": self.s3_settings.endpoint_url,
                },
            },
        }
```

## Validation

Pydantic automatically validates settings values:

```python
class CelerySettings(BaseSettings):
    task_time_limit: int | None = 300  # Must be int or None
    task_serializer: str = "json"       # Must be string
    accept_content: list[str] = Field(default_factory=lambda: ["json"])  # Must be list
```

If environment variables contain invalid values, Pydantic raises a `ValidationError` at startup with clear error messages.

## Environment File Support

Settings can load from `.env` files:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

## Testing with Settings

Override settings in tests by registering instances:

```python
def test_with_custom_settings(container: Container) -> None:
    test_settings = JWTServiceSettings(
        secret_key=SecretStr("test-secret"),
        algorithm="HS256",
        access_token_expire_minutes=5,
    )

    container.register(JWTServiceSettings, instance=test_settings)

    # Services now use test settings
    service = container.resolve(JWTService)
```

## Summary

Pydantic Settings provides:

| Feature | Benefit |
|---------|---------|
| Environment variable loading | Configuration without code changes |
| Type validation | Catch config errors at startup |
| `SecretStr` | Prevent accidental secret exposure |
| Computed properties | Derived values from base config |
| Prefixes | Namespace isolation for different services |
| IoC integration | Settings injected like any other dependency |

Settings classes are the foundation of configuration management in this template. They ensure type safety, secure handling of secrets, and seamless integration with the dependency injection system.
