# Observability

Monitoring, logging, and tracing for production applications.

## Overview

Observability helps you understand what's happening inside your application:

- **Logging** — Structured logs with colorlog
- **Tracing** — Distributed tracing with Logfire (OpenTelemetry)
- **Metrics** — Performance data via OpenTelemetry

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Application                          │
├─────────────┬─────────────────────┬────────────────────┤
│   Logging   │  OpenTelemetry SDK  │  Instrumentation   │
│ (colorlog)  │     (Logfire)       │  (auto-detected)   │
└──────┬──────┴──────────┬──────────┴─────────┬──────────┘
       │                 │                    │
       ▼                 ▼                    ▼
   Console           Logfire             Automatic
    Output          Platform             Tracing
```

## Topics

<div class="grid cards" markdown>

-   **Logging**

    ---

    Console logging with colors and log levels.

    [:octicons-arrow-right-24: Learn More](logging.md)

-   **Logfire (OpenTelemetry)**

    ---

    Distributed tracing with Pydantic's Logfire platform.

    [:octicons-arrow-right-24: Learn More](logfire.md)

-   **Instrumented Libraries**

    ---

    Auto-instrumented libraries for tracing.

    [:octicons-arrow-right-24: Learn More](instrumented-libraries.md)

-   **Sensitive Data Scrubbing**

    ---

    Protecting secrets in traces and logs.

    [:octicons-arrow-right-24: Learn More](scrubbing.md)

</div>

## Quick Start

### Enable Logging

Set the log level:

```bash
LOGGING_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Enable Logfire

1. Sign up at [logfire.pydantic.dev](https://logfire.pydantic.dev/)
2. Get your project token
3. Configure environment:

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your-logfire-token
```

## Bootstrap Sequence

Observability is configured during application startup:

```python
# src/core/configs/infrastructure.py

def configure_infrastructure(service_name: str) -> None:
    load_dotenv(override=False)
    configure_logging()  # Set up logging first

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.configs.django")
    django.setup()

    configure_logfire(  # Then set up tracing
        service_name=service_name,
        environment=application_settings.environment,
        version=application_settings.version,
    )
```

## Service Names

Each entry point has a unique service name for identification:

| Entry Point | Service Name |
|-------------|--------------|
| HTTP API | `http` |
| Telegram Bot | `bot` |
| Celery Worker | `celery-worker` |
| Celery Beat | `celery-beat` |

## Related Topics

- [Production Configuration](../configuration/production.md) — Production settings
- [Docker Compose](../deployment/docker-compose.md) — Container configuration
