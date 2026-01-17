# Environment Variables

All configuration is managed through environment variables using Pydantic Settings.

## Django Core

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Yes | - | Django secret key for cryptographic signing |
| `DJANGO_DEBUG` | No | `false` | Enable debug mode |
| `ENVIRONMENT` | No | `production` | Environment: `local`, `development`, `staging`, `production`, `test`, `ci` |
| `LOGGING_LEVEL` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `ALLOWED_HOSTS` | No | `["localhost", "127.0.0.1"]` | JSON list of allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | No | `["http://localhost"]` | JSON list of trusted CSRF origins |

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///db.sqlite3` | Database connection string (PostgreSQL recommended) |
| `CONN_MAX_AGE` | No | `600` | Database connection max age in seconds |
| `POSTGRES_USER` | Yes* | - | PostgreSQL username (for Docker) |
| `POSTGRES_PASSWORD` | Yes* | - | PostgreSQL password (for Docker) |
| `POSTGRES_DB` | Yes* | - | PostgreSQL database name (for Docker) |

*Required when using Docker Compose.

## Redis

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | - | Redis connection string |
| `REDIS_PASSWORD` | No | - | Redis password (interpolated into `REDIS_URL` in Docker Compose) |
| `CACHE_DEFAULT_TIMEOUT` | No | `300` | Default cache timeout in seconds |

!!! info "REDIS_PASSWORD Usage"
    In Docker Compose, `REDIS_PASSWORD` is interpolated into `REDIS_URL`:
    ```
    REDIS_URL: "redis://default:${REDIS_PASSWORD}@redis:6379/0"
    ```
    Set `REDIS_PASSWORD` in your `.env` file and Docker Compose will automatically construct the complete Redis URL.

## JWT Authentication

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET_KEY` | Yes | - | Secret key for JWT token signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token lifetime in minutes |

## S3/MinIO Storage

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_S3_ENDPOINT_URL` | Yes* | - | S3-compatible endpoint URL |
| `AWS_S3_ACCESS_KEY_ID` | Yes* | - | S3 access key ID |
| `AWS_S3_SECRET_ACCESS_KEY` | Yes* | - | S3 secret access key |
| `AWS_S3_PROTECTED_BUCKET_NAME` | No | `protected` | Private bucket name |
| `AWS_S3_PUBLIC_BUCKET_NAME` | No | `public` | Public bucket name |

*Required when using S3 storage backend.

## Celery

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | No | `1` | Tasks to prefetch per worker |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | No | `1000` | Max tasks before worker restart |
| `CELERY_WORKER_MAX_MEMORY_PER_CHILD` | No | - | Memory limit per worker (KB) |
| `CELERY_TASK_ACKS_LATE` | No | `true` | Acknowledge after execution |
| `CELERY_TASK_REJECT_ON_WORKER_LOST` | No | `true` | Requeue if worker dies |
| `CELERY_TASK_TIME_LIMIT` | No | `300` | Hard time limit (seconds) |
| `CELERY_TASK_SOFT_TIME_LIMIT` | No | `270` | Soft time limit (seconds) |
| `CELERY_RESULT_EXPIRES` | No | `3600` | Result expiry (seconds) |
| `CELERY_RESULT_BACKEND_ALWAYS_RETRY` | No | `true` | Retry on transient errors |
| `CELERY_RESULT_BACKEND_MAX_RETRIES` | No | `10` | Max result backend retries |
| `CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP` | No | `true` | Retry broker on startup |
| `CELERY_BROKER_CONNECTION_MAX_RETRIES` | No | `10` | Max broker connection retries |
| `CELERY_TASK_SERIALIZER` | No | `json` | Task serialization format |
| `CELERY_RESULT_SERIALIZER` | No | `json` | Result serialization format |
| `CELERY_ACCEPT_CONTENT` | No | `["json"]` | Accepted content types |
| `CELERY_WORKER_SEND_TASK_EVENTS` | No | `true` | Send task events (for monitoring) |
| `CELERY_TASK_SEND_SENT_EVENT` | No | `true` | Send sent events |

## HTTP/CORS

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ALLOW_CREDENTIALS` | No | `true` | Allow credentials in CORS |
| `CORS_ALLOWED_ORIGINS` | No | `["http://localhost"]` | JSON list of allowed CORS origins |
| `NUMBER_OF_PROXIES` | No | `0` | Number of reverse proxies |

## Observability (Logfire)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LOGFIRE_ENABLED` | No | `false` | Enable Logfire observability |
| `LOGFIRE_TOKEN` | No | - | Logfire write token |

## Docker Compose

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COMPOSE_FILE` | No | `docker-compose.yaml` | Compose file(s) to use |

For local development, set:

```bash
COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml
```

## Example Configuration

Minimal `.env` for local development:

```bash
COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml

DJANGO_SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

ENVIRONMENT=local
DJANGO_DEBUG=true
LOGGING_LEVEL=DEBUG

POSTGRES_USER=postgres
POSTGRES_DB=postgres
POSTGRES_PASSWORD=your-password
DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"

REDIS_PASSWORD=your-redis-password
REDIS_URL="redis://default:${REDIS_PASSWORD}@localhost:6379/0"

AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=your-access-key
AWS_S3_SECRET_ACCESS_KEY=your-secret-key
```
