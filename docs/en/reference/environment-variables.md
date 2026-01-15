# Environment Variables

Complete reference of all environment variables used by the application.

## Django Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_DEBUG` | `false` | Enable debug mode (never in production) |
| `DJANGO_SECRET_KEY` | **Required** | Secret key for cryptographic signing |
| `DJANGO_ALLOWED_HOSTS` | `*` | Comma-separated list of allowed hosts |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///db.sqlite3` | Database connection URL |
| `DATABASE_CONN_MAX_AGE` | `600` | Connection persistence in seconds |

### Connection URL Format

```
postgres://user:password@host:port/database
```

Examples:

```bash
# Local development
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app

# Production
DATABASE_URL=postgres://appuser:secure_password@db.example.com:5432/production
```

## Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | **Required** | Redis connection URL |

### Connection URL Format

```
redis://[:password@]host:port[/database]
```

Examples:

```bash
# Local development
REDIS_URL=redis://localhost:6379

# With password
REDIS_URL=redis://:mypassword@redis.example.com:6379

# With database selection
REDIS_URL=redis://localhost:6379/1
```

## JWT Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | **Required** | Secret key for signing JWTs |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime in days |

## Celery

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | `1` | Tasks to prefetch per worker |
| `CELERY_WORKER_MAX_TASKS_PER_CHILD` | `1000` | Tasks before worker restart |
| `CELERY_TASK_ACKS_LATE` | `true` | Acknowledge after completion |
| `CELERY_TASK_TIME_LIMIT` | `300` | Hard time limit in seconds |
| `CELERY_TASK_SOFT_TIME_LIMIT` | `270` | Soft time limit in seconds |
| `CELERY_RESULT_EXPIRES` | `3600` | Result expiration in seconds |

## Telegram Bot

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | **Required** | Bot token from @BotFather |
| `TELEGRAM_BOT_PARSE_MODE` | `HTML` | Default message parse mode |

## S3/MinIO Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_S3_ENDPOINT_URL` | - | S3-compatible endpoint URL |
| `AWS_S3_ACCESS_KEY_ID` | - | Access key ID |
| `AWS_S3_SECRET_ACCESS_KEY` | - | Secret access key |
| `AWS_S3_BUCKET_NAME` | - | Default bucket name |
| `AWS_S3_REGION_NAME` | `us-east-1` | Region name |

### Local MinIO Configuration

```bash
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=minioadmin
AWS_S3_SECRET_ACCESS_KEY=minioadmin
AWS_S3_BUCKET_NAME=app-bucket
```

## Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `LOGFIRE_ENABLED` | `false` | Enable Logfire integration |
| `LOGFIRE_TOKEN` | - | Logfire write token |
| `LOGFIRE_PROJECT` | - | Logfire project name |

### Alternative OpenTelemetry Backends

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint |
| `OTEL_EXPORTER_OTLP_HEADERS` | Headers for OTLP (e.g., API keys) |
| `OTEL_SERVICE_NAME` | Service name for traces |

## Cache

| Variable | Default | Description |
|----------|---------|-------------|
| `CACHE_DEFAULT_TIMEOUT` | `300` | Default cache timeout in seconds |

## CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | `[]` | Allowed CORS origins |
| `CORS_ALLOW_ALL_ORIGINS` | `false` | Allow all origins (dev only) |

## Example Configurations

### Development (`.env`)

```bash
# Django
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5432/app

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token

# MinIO
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=minioadmin
AWS_S3_SECRET_ACCESS_KEY=minioadmin
AWS_S3_BUCKET_NAME=app-bucket

# Observability
LOGFIRE_ENABLED=false
```

### Production

```bash
# Django
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_ALLOWED_HOSTS=api.example.com,www.example.com

# Database
DATABASE_URL=postgres://appuser:secure_password@db.example.com:5432/production

# Redis
REDIS_URL=redis://:redis_password@redis.example.com:6379

# JWT
JWT_SECRET_KEY=<strong-random-key>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Celery
CELERY_WORKER_MAX_TASKS_PER_CHILD=500
CELERY_TASK_TIME_LIMIT=300

# S3
AWS_S3_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_S3_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET_NAME=production-bucket
AWS_S3_REGION_NAME=us-east-1

# Observability
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=<your-token>

# CORS
CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
```

### Test (`.env.test`)

```bash
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=test-secret-key

DATABASE_URL=postgres://postgres:postgres@localhost:5432/test_app

REDIS_URL=redis://localhost:6379

JWT_SECRET_KEY=test-jwt-secret

LOGFIRE_ENABLED=false
```

## Generating Secrets

### Django Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### JWT Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Related

- [Pydantic Settings](../concepts/pydantic-settings.md) - How settings are loaded
- [Docker Services](docker-services.md) - Container configuration
