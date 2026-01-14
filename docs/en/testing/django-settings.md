# Django Settings Overrides

Overriding Django settings for test isolation.

## Overview

Integration tests often need to override Django settings to:

- Use isolated cache backends
- Configure test-specific database settings
- Disable external services
- Speed up password hashing

The `pytest-django` plugin provides a `settings` fixture that allows temporary setting overrides.

## The Settings Fixture

pytest-django provides a `SettingsWrapper` that allows modifying Django settings for a single test:

```python
from pytest_django.fixtures import SettingsWrapper


def test_with_custom_setting(settings: SettingsWrapper) -> None:
    settings.DEBUG = True
    settings.MY_CUSTOM_SETTING = "test_value"

    # Test code uses modified settings
    assert settings.DEBUG is True
```

Settings are automatically restored after the test completes.

## Automatic Settings Overrides

Use `autouse=True` fixtures to apply settings to all tests in a module or directory:

```python
from uuid import uuid7

import pytest
from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(scope="function", autouse=True)
def _configure_settings(settings: SettingsWrapper) -> None:
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"test-cache-{uuid7()}",
        },
    }
```

This fixture:

1. Runs automatically for every test (`autouse=True`)
2. Uses function scope for per-test isolation (`scope="function"`)
3. Creates unique cache location per test (`uuid7()`)
4. Uses in-memory cache instead of Redis

## Common Override Patterns

### Isolated Cache

Prevent cache pollution between tests:

```python
from uuid import uuid7


@pytest.fixture(scope="function", autouse=True)
def _isolated_cache(settings: SettingsWrapper) -> None:
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"test-cache-{uuid7()}",
        },
    }
```

### Faster Password Hashing

Speed up tests that create users:

```python
@pytest.fixture(scope="function", autouse=True)
def _fast_password_hasher(settings: SettingsWrapper) -> None:
    settings.PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]
```

### Disable External Services

Prevent accidental external calls:

```python
@pytest.fixture(scope="function", autouse=True)
def _disable_external_services(settings: SettingsWrapper) -> None:
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.CELERY_TASK_ALWAYS_EAGER = True
```

### Override Rate Limiting

Disable throttling for tests:

```python
@pytest.fixture(scope="function", autouse=True)
def _disable_throttling(settings: SettingsWrapper) -> None:
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
    }
```

## Conditional Overrides

Apply overrides based on test markers:

```python
import pytest
from pytest_django.fixtures import SettingsWrapper


@pytest.fixture(scope="function", autouse=True)
def _configure_debug(request: pytest.FixtureRequest, settings: SettingsWrapper) -> None:
    if request.node.get_closest_marker("debug_mode"):
        settings.DEBUG = True


@pytest.mark.debug_mode
def test_with_debug_enabled(settings: SettingsWrapper) -> None:
    assert settings.DEBUG is True


def test_without_debug(settings: SettingsWrapper) -> None:
    assert settings.DEBUG is False
```

## Per-Test Overrides

Override settings in individual tests:

```python
def test_with_debug(settings: SettingsWrapper) -> None:
    settings.DEBUG = True
    # Test with DEBUG=True


def test_without_debug(settings: SettingsWrapper) -> None:
    settings.DEBUG = False
    # Test with DEBUG=False
```

## Fixture Placement

Place settings fixtures in `conftest.py` for appropriate scope:

```
tests/
├── conftest.py              # Project-wide settings overrides
└── integration/
    ├── conftest.py          # Integration test settings
    └── http/
        ├── conftest.py      # HTTP-specific settings
        └── test_api.py
```

Settings fixtures in nested `conftest.py` files override parent fixtures.

## Best Practices

### 1. Use Unique Identifiers

For caches and sessions, use unique identifiers to prevent test interference:

```python
from uuid import uuid7

settings.CACHES["default"]["LOCATION"] = f"test-{uuid7()}"
```

### 2. Prefer In-Memory Backends

Use in-memory backends for speed and isolation:

```python
# Cache
"BACKEND": "django.core.cache.backends.locmem.LocMemCache"

# Email
"EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend"

# Sessions
"SESSION_ENGINE": "django.contrib.sessions.backends.cache"
```

### 3. Document Required Settings

Add comments explaining why settings are overridden:

```python
@pytest.fixture(scope="function", autouse=True)
def _configure_settings(settings: SettingsWrapper) -> None:
    # Use isolated in-memory cache to prevent test pollution
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": f"test-cache-{uuid7()}",
        },
    }
```

### 4. Combine with IoC Overrides

Settings overrides work alongside IoC container mocking:

```python
def test_with_both_overrides(
    settings: SettingsWrapper,
    container: Container,
) -> None:
    # Override Django setting
    settings.DEBUG = True

    # Override IoC dependency
    mock_service = MagicMock()
    container.register(MyService, instance=mock_service)

    # Both overrides apply to this test
```

## Related Topics

- [Mocking IoC Dependencies](mocking-ioc.md) — Container overrides
- [Test Factories](test-factories.md) — Factory setup
- [HTTP API Tests](http-tests.md) — Testing endpoints
