# Logging

Console logging with colors and configurable levels.

## Overview

The logging system uses:

- **colorlog** — Colored console output
- **Pydantic Settings** — Type-safe configuration
- **Python logging** — Standard library integration

## Configuration

```python
# src/infrastructure/logging/configuration.py

class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGGING_")

    level: str = "INFO"
```

### Environment Variable

```bash
LOGGING_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Log Levels

| Level | Value | Usage |
|-------|-------|-------|
| `DEBUG` | 10 | Detailed information for debugging |
| `INFO` | 20 | General operational information |
| `WARNING` | 30 | Something unexpected happened |
| `ERROR` | 40 | A more serious problem |
| `CRITICAL` | 50 | Program may not be able to continue |

## Log Format

```
2024-01-15 10:30:45 INFO delivery.http.user.controllers User created: user@example.com
```

Format: `%(asctime)s %(levelname)s %(name)s %(message)s`

## Colored Output

The colorlog formatter adds colors to log levels:

```python
"colored": {
    "()": "colorlog.ColoredFormatter",
    "format": "%(asctime)s %(log_color)s%(levelname)s %(name)s %(message)s",
    "datefmt": "%Y-%m-%d %H:%M:%S",
},
```

| Level | Color |
|-------|-------|
| DEBUG | Cyan |
| INFO | Green |
| WARNING | Yellow |
| ERROR | Red |
| CRITICAL | Bold Red |

## Logger Configuration

```python
@computed_field()
def settings(self) -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {...},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console"],
                "level": self.level,
                "propagate": True,
            },
            # Suppress noisy loggers
            "urllib3": {"level": "WARNING"},
            "opentelemetry.instrumentation.instrumentor": {"level": "ERROR"},
        },
    }
```

## Using Loggers

### Basic Usage

```python
import logging

logger = logging.getLogger(__name__)


def my_function():
    logger.info("Function started")
    logger.debug("Processing data: %s", data)
    logger.warning("Unexpected value: %s", value)
    logger.error("Operation failed: %s", error)
```

### In Controllers

```python
import logging

logger = logging.getLogger(__name__)


class UserController(Controller):
    def create_user(self, request: HttpRequest, body: CreateUserSchema) -> UserSchema:
        logger.info("Creating user: %s", body.username)

        user = User.objects.create_user(...)

        logger.info("User created: id=%d", user.id)
        return UserSchema.model_validate(user, from_attributes=True)
```

### In Services

```python
import logging

logger = logging.getLogger(__name__)


class JWTService:
    def decode_token(self, token: str) -> dict[str, Any]:
        logger.debug("Decoding token")
        try:
            payload = jwt.decode(...)
            logger.debug("Token decoded: sub=%s", payload.get("sub"))
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise
```

## Suppressing Noisy Loggers

Configure specific loggers to reduce noise:

```python
"loggers": {
    # Suppress urllib3 connection logs
    "urllib3": {"level": "WARNING"},

    # Suppress OpenTelemetry instrumentation logs
    "opentelemetry.instrumentation.instrumentor": {"level": "ERROR"},

    # Suppress Django's SQL logging
    "django.db.backends": {"level": "WARNING"},
}
```

## Best Practices

### 1. Use Appropriate Levels

```python
# Good: Meaningful log levels
logger.debug("Cache hit for key: %s", key)
logger.info("User logged in: %s", username)
logger.warning("Rate limit approaching: %d/%d", current, limit)
logger.error("Database connection failed: %s", error)

# Avoid: Everything at INFO
logger.info("Checking cache...")
logger.info("Found in cache")
logger.info("Returning result")
```

### 2. Include Context

```python
# Good: Useful context
logger.info("Order created: order_id=%d, user_id=%d, total=%.2f", order.id, user.id, total)

# Avoid: Missing context
logger.info("Order created")
```

### 3. Don't Log Secrets

```python
# Good: Mask sensitive data
logger.info("User authenticated: %s", username)

# Avoid: Logging secrets
logger.info("Token: %s", token)  # Never!
logger.info("Password: %s", password)  # Never!
```

### 4. Use String Formatting

```python
# Good: Lazy evaluation (only formatted if logged)
logger.debug("Processing item: %s", item)

# Avoid: Eager evaluation (always formatted)
logger.debug(f"Processing item: {item}")
```

## Development vs Production

### Development

```bash
LOGGING_LEVEL=DEBUG
```

Shows all logs including debug information.

### Production

```bash
LOGGING_LEVEL=INFO
```

Shows operational logs without debug noise.

## Related Topics

- [Logfire](logfire.md) — Distributed tracing
- [Production Configuration](../configuration/production.md) — Production settings
