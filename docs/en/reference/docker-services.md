# Docker Services

The application uses Docker Compose for containerized deployment.

## Service Overview

| Service | Image | Purpose | Ports |
|---------|-------|---------|-------|
| `api` | `base:local` | Django Ninja HTTP API | 8009:8000 |
| `celery-worker` | `base:local` | Background task processing | - |
| `celery-beat` | `base:local` | Periodic task scheduler | - |
| `bot` | `base:local` | Telegram bot | - |
| `migrations` | `base:local` | Database migrations (run-once) | - |
| `collectstatic` | `base:local` | Static file collection (run-once) | - |
| `postgres` | `postgres:18-alpine` | Primary database | 5432* |
| `pgbouncer` | `edoburu/pgbouncer` | Connection pooling | - |
| `redis` | `redis:latest` | Celery broker and cache | 6379* |
| `minio` | `minio/minio` | S3-compatible storage | 9000, 9001 |
| `minio-create-buckets` | `minio/mc` | Bucket initialization (run-once) | - |

*Ports exposed only in local development configuration.

## Compose Files

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Production configuration |
| `docker-compose.local.yaml` | Local development overrides |

For local development, use both files:

```bash
export COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml
```

Or set in `.env`:

```bash
COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml
```

## Common Operations

### Start Infrastructure

```bash
# Start all infrastructure services
docker compose up -d postgres redis minio

# Initialize (migrations, buckets, static files)
docker compose up minio-create-buckets migrations collectstatic
```

### Start Application

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d api
docker compose up -d celery-worker
docker compose up -d bot
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f celery-worker
```

### Stop Services

```bash
# Stop all
docker compose down

# Stop and remove volumes
docker compose down -v
```

### Rebuild

```bash
# Rebuild base image
docker compose build base

# Rebuild and restart
docker compose up -d --build api
```

## Service Details

### api

Django Ninja HTTP API served by Gunicorn.

| Setting | Value |
|---------|-------|
| Workers | 4 |
| Timeout | 120s |
| Bind | 0.0.0.0:8000 |

Production command:

```bash
gunicorn delivery.http.app:wsgi --workers=4 --bind=0.0.0.0 --timeout=120
```

Local development uses Django's runserver with volume mounts.

### celery-worker

Background task processor.

| Setting | Production | Local |
|---------|------------|-------|
| Concurrency | 4 | 2 |
| Log Level | `${LOGGING_LEVEL:-INFO}` | `${LOGGING_LEVEL:-INFO}` |
| Auto-reload | No | Yes (watchmedo) |

### celery-beat

Periodic task scheduler for scheduled jobs.

### bot

Telegram bot running in long-polling mode.

### postgres

PostgreSQL 18 database.

| Setting | Value |
|---------|-------|
| Auth Method | scram-sha-256 |
| Volume | `postgres_data` |

### pgbouncer

Connection pooler for PostgreSQL.

| Setting | Value |
|---------|-------|
| Pool Mode | transaction |
| Max Client Connections | 200 |
| Default Pool Size | 25 |
| Min Pool Size | 5 |
| Server Lifetime | 3600s |
| Server Idle Timeout | 600s |
| Auth Type | scram-sha-256 |

!!! info "Authentication"
    PgBouncer is configured with `AUTH_TYPE: scram-sha-256` to match PostgreSQL's authentication method. This ensures secure password hashing between PgBouncer and PostgreSQL. Both services must use the same authentication method for connections to succeed.

### redis

Redis for Celery broker and Django cache.

| Setting | Value |
|---------|-------|
| Volume | `redis_data` |

### minio

S3-compatible object storage.

| Port | Purpose |
|------|---------|
| 9000 | API endpoint |
| 9001 | Web console |

### minio-create-buckets

Initializes storage buckets on first run:

| Bucket | Access |
|--------|--------|
| `protected` | Private |
| `public` | Public read |

## Networking

All services connect via the `main` bridge network. Internal DNS resolves service names:

| Service | Internal Hostname |
|---------|-------------------|
| PostgreSQL | `postgres:5432` |
| PgBouncer | `pgbouncer:5432` |
| Redis | `redis:6379` |
| MinIO | `minio:9000` |

Application services connect to PgBouncer (not directly to PostgreSQL) for connection pooling.

## Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data |
| `redis_data` | Redis persistence |
| `minio_data` | Object storage |

## Health Checks

| Service | Check | Interval |
|---------|-------|----------|
| postgres | `pg_isready` | 10s |
| pgbouncer | `pg_isready` | 10s |
| minio | HTTP `/minio/health/live` | 2s |

## Dependencies

```
api
  -> pgbouncer -> postgres
  -> migrations -> pgbouncer
  -> collectstatic -> minio-create-buckets -> minio
  -> celery-worker -> redis

celery-worker
  -> pgbouncer
  -> migrations
  -> redis

celery-beat
  -> pgbouncer
  -> migrations
  -> redis

bot
  -> pgbouncer
  -> migrations
```
