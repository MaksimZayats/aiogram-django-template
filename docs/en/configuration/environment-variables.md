# Environment Variables

Complete reference of all environment variables.

## Core Django

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DJANGO_SECRET_KEY` | `SecretStr` | **Required** | Django secret key for cryptographic signing |
| `DJANGO_DEBUG` | `bool` | `false` | Enable debug mode (never in production) |
| `ENVIRONMENT` | `str` | `production` | Environment: `local`, `staging`, `production` |

## HTTP Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALLOWED_HOSTS` | `list[str]` | `["localhost", "127.0.0.1"]` | Allowed host headers |
| `CSRF_TRUSTED_ORIGINS` | `list[str]` | `["http://localhost"]` | Trusted origins for CSRF |

!!! note "List Format"
    Lists are JSON arrays: `ALLOWED_HOSTS='["example.com", "api.example.com"]'`

## Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | `str` | `sqlite:///db.sqlite3` | Database connection URL |
| `CONN_MAX_AGE` | `int` | `600` | Database connection max age (seconds) |

### Database URL Format

```
postgres://user:password@host:port/database
```

Components:

- `postgres://` — Database driver
- `user:password` — Credentials
- `host:port` — Server address (default port: 5432)
- `database` — Database name

## JWT Authentication

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `JWT_SECRET_KEY` | `SecretStr` | **Required** | JWT signing key |
| `JWT_ALGORITHM` | `str` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | Access token TTL |

## Refresh Tokens

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REFRESH_TOKEN_NBYTES` | `int` | `32` | Refresh token entropy |
| `REFRESH_TOKEN_TTL_DAYS` | `int` | `30` | Refresh token TTL |
| `IP_HEADER` | `str` | `X-Forwarded-For` | Header for client IP |

## Redis

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | `SecretStr` | **Required for Celery** | Redis connection URL |

### Redis URL Format

```
redis://username:password@host:port/database
```

## Telegram Bot

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | **Required for bot** | Bot token from BotFather |
| `TELEGRAM_BOT_PARSE_MODE` | `str` | `HTML` | Default message parse mode |

## S3/MinIO Storage

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AWS_S3_ENDPOINT_URL` | `str` | **Required** | S3/MinIO endpoint URL |
| `AWS_S3_ACCESS_KEY_ID` | `str` | **Required** | Access key ID |
| `AWS_S3_SECRET_ACCESS_KEY` | `SecretStr` | **Required** | Secret access key |
| `AWS_S3_PROTECTED_BUCKET_NAME` | `str` | `protected` | Protected bucket name |
| `AWS_S3_PUBLIC_BUCKET_NAME` | `str` | `public` | Public bucket name |

## Observability

### Logging

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOGGING_LEVEL` | `str` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR |

### Logfire (OpenTelemetry)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LOGFIRE_ENABLED` | `bool` | `false` | Enable Logfire telemetry |
| `LOGFIRE_TOKEN` | `SecretStr` | None | Logfire API token |

## Docker Compose Variables

These are used by `docker-compose.yaml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_FILE` | `docker-compose.yaml` | Compose files to use |
| `POSTGRES_USER` | — | PostgreSQL username |
| `POSTGRES_PASSWORD` | — | PostgreSQL password |
| `POSTGRES_DB` | — | PostgreSQL database name |
| `REDIS_PASSWORD` | — | Redis password |

## Example .env File

```bash
# Docker Compose
COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml

# Django
DJANGO_SECRET_KEY=your-super-secret-key-change-in-production
DJANGO_DEBUG=true
ENVIRONMENT=local

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Logging
LOGGING_LEVEL=DEBUG

# HTTP
ALLOWED_HOSTS='["127.0.0.1", "localhost"]'
CSRF_TRUSTED_ORIGINS='["http://localhost"]'

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_DB=postgres
POSTGRES_PASSWORD=your-postgres-password
DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"

# Redis
REDIS_PASSWORD=your-redis-password
REDIS_URL="redis://default:${REDIS_PASSWORD}@localhost:6379/0"

# S3/MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=your-minio-access-key
AWS_S3_SECRET_ACCESS_KEY=your-minio-secret-key

# Telegram Bot (optional)
# TELEGRAM_BOT_TOKEN=your-bot-token

# Observability (optional)
# LOGFIRE_ENABLED=true
# LOGFIRE_TOKEN=your-logfire-token
```

## Secret Generation

Generate secure secrets for production:

```bash
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generic secret (32 bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Related Topics

- [Production Configuration](production.md) — Production settings
- [Pydantic Settings](../concepts/pydantic-settings.md) — How settings work
