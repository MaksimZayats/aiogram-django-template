# Django Settings Adapter

How Pydantic settings are adapted to Django's expected format.

## The Problem

Django expects settings as module-level variables in UPPER_CASE:

```python
# Django's expectation
SECRET_KEY = "..."
DEBUG = False
DATABASES = {...}
```

Pydantic Settings uses class attributes with lowercase names:

```python
class SecuritySettings(BaseSettings):
    secret_key: SecretStr
    debug: bool = False
```

## The Solution

The `PydanticSettingsAdapter` bridges this gap by converting Pydantic settings to Django's format.

### Implementation

```python
# src/infrastructure/django/settings/pydantic_adapter.py

class PydanticSettingsAdapter:
    def adapt(
        self,
        *settings: BaseSettings,
        settings_locals: dict[str, Any],
    ) -> None:
        for setting in settings:
            self._adapt(settings=setting, settings_locals=settings_locals)

    def _adapt(
        self,
        settings: BaseSettings,
        settings_locals: dict[str, Any],
    ) -> None:
        for key, value in settings.model_dump().items():
            resolved_key = self._resolve_key(key)
            resolved_value = self._resolve_value(value)
            settings_locals[resolved_key] = resolved_value

    def _resolve_key(self, key: str) -> str:
        return key.upper()

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, (SecretStr, SecretBytes)):
            return value.get_secret_value()
        return value
```

### Usage

In `src/core/configs/django.py`:

```python
from infrastructure.django.settings.pydantic_adapter import PydanticSettingsAdapter

# Instantiate settings
application_settings = ApplicationSettings()
security_settings = SecuritySettings()
database_settings = DatabaseSettings()
storage_settings = StorageSettings()
logging_settings = LoggingConfig()
http_settings = HTTPSettings()
auth_settings = AuthSettings()
template_settings = TemplateSettings()

# Adapt to Django format
adapter = PydanticSettingsAdapter()
adapter.adapt(
    database_settings,
    application_settings,
    security_settings,
    storage_settings,
    logging_settings,
    http_settings,
    template_settings,
    auth_settings,
    settings_locals=locals(),
)
```

## How It Works

### 1. Key Transformation

Pydantic field names are converted to UPPER_CASE:

```python
secret_key → SECRET_KEY
debug → DEBUG
allowed_hosts → ALLOWED_HOSTS
```

### 2. Value Unwrapping

`SecretStr` values are automatically unwrapped:

```python
# Pydantic
secret_key: SecretStr = "my-secret"

# Django (after adaptation)
SECRET_KEY = "my-secret"  # Unwrapped
```

### 3. Complex Types

Nested structures and computed fields pass through unchanged:

```python
# Pydantic
@computed_field()
def databases(self) -> dict[str, Any]:
    return {"default": {...}}

# Django
DATABASES = {"default": {...}}
```

## Settings Classes

The following classes are adapted:

| Class | Fields Adapted |
|-------|----------------|
| `DatabaseSettings` | `databases`, `default_auto_field`, `conn_max_age` |
| `ApplicationSettings` | `installed_apps`, `language_code`, `time_zone`, `use_tz` |
| `SecuritySettings` | `secret_key`, `debug` |
| `StorageSettings` | `static_url`, `media_url`, `storages` |
| `LoggingConfig` | `logging_settings` (becomes `LOGGING`) |
| `HTTPSettings` | `allowed_hosts`, `csrf_trusted_origins`, `middleware`, etc. |
| `AuthSettings` | `auth_user_model`, `authentication_backends`, `password_validators` |
| `TemplateSettings` | `templates` |

## Example: Database Settings

### Pydantic Definition

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

### After Adaptation

```python
# These are now available as Django settings
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CONN_MAX_AGE = 600
DATABASE_URL = "sqlite:///db.sqlite3"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "mydb",
        "USER": "user",
        # ...
    }
}
```

## Benefits

### Type Safety

Settings are validated at startup:

```python
class SecuritySettings(BaseSettings):
    secret_key: SecretStr  # Required, will fail if missing
    debug: bool = False    # Must be boolean
```

### Centralized Configuration

All settings in one place with clear organization:

```python
# src/core/configs/django.py
application_settings = ApplicationSettings()  # App config
security_settings = SecuritySettings()        # Security config
database_settings = DatabaseSettings()        # Database config
```

### Environment Variable Support

Settings automatically read from environment:

```bash
# .env
DJANGO_SECRET_KEY=my-secret
DJANGO_DEBUG=false
```

### Secret Protection

`SecretStr` prevents accidental logging:

```python
>>> print(settings.secret_key)
**********

>>> print(settings.secret_key.get_secret_value())
my-secret  # Only when explicitly requested
```

## Limitations

### Order Matters

Settings are applied in order, so later settings can override earlier ones if field names conflict.

### No Lazy Evaluation

All settings are evaluated at import time, not on first access.

## Related Topics

- [Pydantic Settings](../concepts/pydantic-settings.md) — Settings pattern
- [Environment Variables](environment-variables.md) — All variables
- [Production Configuration](production.md) — Production settings
