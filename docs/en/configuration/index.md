# Configuration

Configure your application using environment variables and Pydantic settings.

## Overview

This template uses a layered configuration approach:

```
Environment Variables (.env file)
         │
         ▼
Pydantic Settings Classes
         │
         ▼
Django Settings (via Adapter)
         │
         ▼
Application Components
```

## Configuration Sources

<div class="grid cards" markdown>

-   **Environment Variables**

    ---

    All configuration via environment variables with sensible defaults.

    [→ Environment Variables](environment-variables.md)

-   **Django Settings Adapter**

    ---

    How Pydantic settings are adapted to Django's format.

    [→ Django Adapter](django-adapter.md)

-   **Production Configuration**

    ---

    Security settings and best practices for production.

    [→ Production](production.md)

</div>

## Quick Reference

### Essential Variables

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=false

# JWT Authentication
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgres://user:pass@host:5432/db

# Redis (Celery broker/backend)
REDIS_URL=redis://default:pass@host:6379/0

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
```

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Local development configuration |
| `.env.example` | Template with example values |
| `.env.test` | Test environment configuration |

## Settings Classes

| Class | Prefix | Module |
|-------|--------|--------|
| `SecuritySettings` | `DJANGO_` | `core/configs/core.py` |
| `ApplicationSettings` | None | `core/configs/core.py` |
| `DatabaseSettings` | None | `core/configs/core.py` |
| `JWTServiceSettings` | `JWT_` | `infrastructure/jwt/services.py` |
| `TelegramBotSettings` | `TELEGRAM_BOT_` | `delivery/bot/settings.py` |
| `CelerySettings` | `CELERY_` | `delivery/tasks/settings.py` |
| `LogfireSettings` | `LOGFIRE_` | `infrastructure/otel/logfire.py` |
| `LoggingConfig` | `LOGGING_` | `infrastructure/logging/configuration.py` |

## Next Steps

- See [Environment Variables](environment-variables.md) for all options
- See [Production Configuration](production.md) for deployment settings
