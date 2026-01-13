# Logfire (OpenTelemetry)

Distributed tracing with Pydantic's Logfire platform.

## What is Logfire?

[Logfire](https://logfire.pydantic.dev/) is Pydantic's observability platform built on OpenTelemetry. It provides:

- Distributed tracing
- Automatic instrumentation
- Structured logging
- Performance metrics

## Configuration

```python
# src/infrastructure/otel/logfire.py

class LogfireSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGFIRE_")

    enabled: bool = False
    token: SecretStr | None = None
```

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOGFIRE_ENABLED` | `bool` | `false` | Enable Logfire |
| `LOGFIRE_TOKEN` | `SecretStr` | None | Logfire API token |

### Setup

```python
def configure_logfire(
    service_name: str,
    environment: Environment,
    version: str,
) -> None:
    settings = LogfireSettings()
    if not settings.enabled or settings.token is None:
        return

    logfire.configure(
        service_name=service_name,
        service_version=version,
        environment=environment,
        token=settings.token.get_secret_value(),
        scrubbing=ScrubbingOptions(
            extra_patterns=[
                "access_token",
                "refresh_token",
            ],
        ),
    )

    _instrument_libraries()
```

## Getting Started

### 1. Create Account

Sign up at [logfire.pydantic.dev](https://logfire.pydantic.dev/)

### 2. Get Token

Create a project and get your write token.

### 3. Configure Environment

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your-logfire-token
```

### 4. View Traces

Open the Logfire dashboard to see your traces.

## Service Identification

Each service is identified by:

| Field | Source | Example |
|-------|--------|---------|
| `service_name` | Entry point | `http`, `bot`, `celery-worker` |
| `service_version` | `ApplicationSettings.version` | `0.1.0` |
| `environment` | `ApplicationSettings.environment` | `production` |

## Manual Spans

Add custom spans for important operations:

```python
import logfire


def process_order(order_id: int) -> None:
    with logfire.span("process_order", order_id=order_id):
        # Validate order
        with logfire.span("validate_order"):
            validate(order_id)

        # Process payment
        with logfire.span("process_payment"):
            process_payment(order_id)

        # Send confirmation
        with logfire.span("send_confirmation"):
            send_confirmation(order_id)
```

## Structured Logging

Use logfire for structured logs:

```python
import logfire

# Structured log with context
logfire.info("Order created", order_id=123, user_id=456, total=99.99)

# Warning with exception
try:
    risky_operation()
except Exception as e:
    logfire.warning("Operation failed", exc_info=e, operation="risky")

# Error with full trace
logfire.error("Critical failure", error=str(e))
```

## Tracing HTTP Requests

HTTP requests are automatically traced:

```
[HTTP] POST /v1/users/
├── [DB] SELECT * FROM users WHERE username = ?
├── [DB] INSERT INTO users (...)
└── [HTTP] 200 OK (150ms)
```

## Tracing Celery Tasks

Celery tasks show the full execution:

```
[Task] cleanup_sessions
├── [DB] SELECT * FROM sessions WHERE expires_at < ?
├── [DB] DELETE FROM sessions WHERE ...
└── [Task] SUCCESS (2.3s)
```

## Dashboard Features

### Trace View

See request flow across services:

```
API Request → Database → Redis → Response
```

### Performance Metrics

- Request latency percentiles
- Error rates
- Throughput

### Filtering

Filter by:

- Service name
- Environment
- Time range
- Error status
- Custom attributes

## Integration with Logging

Logfire integrates with Python logging:

```python
import logging

logger = logging.getLogger(__name__)

# These logs appear in Logfire traces
logger.info("Processing started")
logger.warning("Slow query detected")
```

## Best Practices

### 1. Use Meaningful Span Names

```python
# Good: Descriptive names
with logfire.span("validate_user_email"):
    ...

# Avoid: Generic names
with logfire.span("operation"):
    ...
```

### 2. Add Context to Spans

```python
with logfire.span("process_order", order_id=id, user_id=user.id):
    ...
```

### 3. Mark Errors

```python
try:
    process()
except Exception as e:
    logfire.error("Processing failed", exc_info=e)
    raise
```

## Related Topics

- [Instrumented Libraries](instrumented-libraries.md) — Auto-instrumentation
- [Sensitive Data Scrubbing](scrubbing.md) — Data protection
- [Logging](logging.md) — Console logging
