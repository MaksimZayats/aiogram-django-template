# Environment Variables

Complete reference of all environment variables.

## Core Django

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DJANGO_SECRET_KEY` | `SecretStr` | — | Yes | Django secret key for cryptographic signing |
| `DJANGO_DEBUG` | `bool` | `false` | No | Enable debug mode (never in production) |
| `ENVIRONMENT` | `str` | `production` | No | Environment: `local`, `staging`, `production` |

## HTTP Settings

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `ALLOWED_HOSTS` | `list[str]` | `["localhost", "127.0.0.1"]` | No | Allowed host headers |
| `CSRF_TRUSTED_ORIGINS` | `list[str]` | `["http://localhost"]` | No | Trusted origins for CSRF |

!!! note "List Format"
    Lists are JSON arrays: `ALLOWED_HOSTS='["example.com", "api.example.com"]'`

## Database

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | `str` | `sqlite:///db.sqlite3` | No | Database connection URL |
| `CONN_MAX_AGE` | `int` | `600` | No | Database connection max age (seconds) |

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

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `JWT_SECRET_KEY` | `SecretStr` | — | Yes | JWT signing key |
| `JWT_ALGORITHM` | `str` | `HS256` | No | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | No | Access token TTL (minutes) |

## Refresh Tokens

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `REFRESH_TOKEN_NBYTES` | `int` | `32` | No | Refresh token entropy (bytes) |
| `REFRESH_TOKEN_TTL_DAYS` | `int` | `30` | No | Refresh token TTL (days) |

## Rate Limiting (Ninja)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `NINJA_NUM_PROXIES` | `int` | `0` | No | Number of trusted proxies for IP extraction |
| `NINJA_DEFAULT_THROTTLE_RATES` | `dict` | See below | No | Global throttle rate defaults |

### Default Throttle Rates

```python
{
    "auth": "10000/day",
    "user": "10000/day",
    "anon": "1000/day",
}
```

!!! note "Rate Format"
    Rates use the format `"N/period"` where period is `s`/`sec`, `m`/`min`, `h`/`hour`, or `d`/`day`.

!!! tip "Proxy Configuration"
    Set `NINJA_NUM_PROXIES` to the number of reverse proxies (Nginx, load balancers) in front of your application. This ensures correct client IP extraction for rate limiting. See [Rate Limiting](../http/rate-limiting.md#ip-address-extraction) for details.

## Cache

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `CACHE_DEFAULT_TIMEOUT` | `int` | `300` | No | Default cache timeout (seconds) |

!!! note "Cache Backend"
    The cache uses Redis (same `REDIS_URL` as Celery). This enables distributed rate limiting across multiple application instances.

## Redis

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `REDIS_URL` | `SecretStr` | — | For Celery | Redis connection URL |

### Redis URL Format

```
redis://username:password@host:port/database
```

## Telegram Bot

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | — | For Bot | Bot token from BotFather |
| `TELEGRAM_BOT_PARSE_MODE` | `str` | `HTML` | No | Default message parse mode |

## S3/MinIO Storage

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `AWS_S3_ENDPOINT_URL` | `str` | — | Yes | S3/MinIO endpoint URL |
| `AWS_S3_ACCESS_KEY_ID` | `str` | — | Yes | Access key ID |
| `AWS_S3_SECRET_ACCESS_KEY` | `SecretStr` | — | Yes | Secret access key |
| `AWS_S3_PROTECTED_BUCKET_NAME` | `str` | `protected` | No | Protected bucket name |
| `AWS_S3_PUBLIC_BUCKET_NAME` | `str` | `public` | No | Public bucket name |

## Observability

### Logging

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `LOGGING_LEVEL` | `str` | `INFO` | No | Log level: DEBUG, INFO, WARNING, ERROR |

### Logfire (OpenTelemetry)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `LOGFIRE_ENABLED` | `bool` | `false` | No | Enable Logfire telemetry |
| `LOGFIRE_TOKEN` | `SecretStr` | — | If enabled | Logfire API token |

## Docker Compose Variables

These are used by `docker-compose.yaml`:

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `COMPOSE_FILE` | `str` | `docker-compose.yaml` | No | Compose files to use |
| `POSTGRES_USER` | `str` | — | For Docker | PostgreSQL username |
| `POSTGRES_PASSWORD` | `str` | — | For Docker | PostgreSQL password |
| `POSTGRES_DB` | `str` | — | For Docker | PostgreSQL database name |
| `REDIS_PASSWORD` | `str` | — | For Docker | Redis password |

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

# Rate Limiting (optional)
# NINJA_NUM_PROXIES=1  # Set to number of proxies in front of app

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
