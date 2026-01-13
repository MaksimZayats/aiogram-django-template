# Environment Variables Reference

Complete reference of all environment variables.

## Django

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DJANGO_SECRET_KEY` | `SecretStr` | — | Yes | Cryptographic signing key |
| `DJANGO_DEBUG` | `bool` | `false` | No | Enable debug mode |
| `ENVIRONMENT` | `str` | `production` | No | `local`, `staging`, `production` |

## HTTP

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `ALLOWED_HOSTS` | `list[str]` | `["localhost", "127.0.0.1"]` | No | Allowed HTTP host headers |
| `CSRF_TRUSTED_ORIGINS` | `list[str]` | `["http://localhost"]` | No | CSRF trusted origins |

## Database

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `DATABASE_URL` | `str` | `sqlite:///db.sqlite3` | No | Database connection URL |
| `CONN_MAX_AGE` | `int` | `600` | No | Connection max age (seconds) |
| `POSTGRES_USER` | `str` | — | For Docker | PostgreSQL username |
| `POSTGRES_PASSWORD` | `str` | — | For Docker | PostgreSQL password |
| `POSTGRES_DB` | `str` | — | For Docker | PostgreSQL database name |

## JWT Authentication

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `JWT_SECRET_KEY` | `SecretStr` | — | Yes | JWT signing key |
| `JWT_ALGORITHM` | `str` | `HS256` | No | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | No | Access token TTL (minutes) |

## Refresh Tokens

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `REFRESH_TOKEN_NBYTES` | `int` | `32` | No | Token entropy (bytes) |
| `REFRESH_TOKEN_TTL_DAYS` | `int` | `30` | No | Token lifetime (days) |
| `IP_HEADER` | `str` | `X-Forwarded-For` | No | Client IP header |

## Redis

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `REDIS_URL` | `SecretStr` | — | For Celery | Redis connection URL |
| `REDIS_PASSWORD` | `str` | — | For Docker | Redis password |

## Telegram Bot

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | `SecretStr` | — | For Bot | Bot token from BotFather |
| `TELEGRAM_BOT_PARSE_MODE` | `str` | `HTML` | No | Message parse mode |

## S3/MinIO Storage

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `AWS_S3_ENDPOINT_URL` | `str` | — | Yes | S3/MinIO endpoint |
| `AWS_S3_ACCESS_KEY_ID` | `str` | — | Yes | Access key ID |
| `AWS_S3_SECRET_ACCESS_KEY` | `SecretStr` | — | Yes | Secret access key |
| `AWS_S3_PROTECTED_BUCKET_NAME` | `str` | `protected` | No | Protected bucket |
| `AWS_S3_PUBLIC_BUCKET_NAME` | `str` | `public` | No | Public bucket |

## Logging

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `LOGGING_LEVEL` | `str` | `INFO` | No | Log level |

## Logfire (OpenTelemetry)

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `LOGFIRE_ENABLED` | `bool` | `false` | No | Enable Logfire |
| `LOGFIRE_TOKEN` | `SecretStr` | — | If enabled | Logfire API token |

## Docker Compose

| Variable | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `COMPOSE_FILE` | `str` | `docker-compose.yaml` | No | Compose files to use |

## URL Formats

### Database URL

```
postgres://user:password@host:port/database
```

### Redis URL

```
redis://username:password@host:port/database
```

For TLS:

```
rediss://username:password@host:port/database
```

## JSON List Format

For list-type variables:

```bash
ALLOWED_HOSTS='["example.com", "api.example.com"]'
```
