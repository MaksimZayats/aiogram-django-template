# Docker Compose

Container orchestration and service configuration.

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Production configuration |
| `docker-compose.local.yaml` | Local development overrides |
| `Dockerfile` | Application container |

## Services Overview

### Application Services

```yaml
services:
  api:
    image: base:local
    ports:
      - "8009:8000"
    command:
      - gunicorn
      - delivery.http.app:wsgi
      - --workers=4
      - --bind=0.0.0.0
      - --timeout=120

  celery-worker:
    image: base:local
    command:
      - celery
      - --app=delivery.tasks.app
      - worker
      - --loglevel=${LOGGING_LEVEL:-INFO}
      - --concurrency=4

  celery-beat:
    image: base:local
    command:
      - celery
      - --app=delivery.tasks.app
      - beat
      - --loglevel=${LOGGING_LEVEL:-INFO}

  bot:
    image: base:local
    command: python -m delivery.bot
```

### Infrastructure Services

```yaml
services:
  postgres:
    image: postgres:18-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql

  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 200
      DEFAULT_POOL_SIZE: 25

  redis:
    image: redis:latest
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
```

## Common Configuration

All application services share common configuration:

```yaml
x-common: &common
  image: base:local
  env_file:
    - .env
  environment:
    DATABASE_URL: "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@pgbouncer:5432/${POSTGRES_DB}"
    AWS_S3_ENDPOINT_URL: "http://minio:9000"
    REDIS_URL: "redis://default:${REDIS_PASSWORD}@redis:6379/0"
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
  networks:
    - main
```

## Building

### Build All Services

```bash
docker compose build
```

### Build Specific Service

```bash
docker compose build api
```

### No Cache Build

```bash
docker compose build --no-cache
```

## Starting Services

### Start All

```bash
docker compose up -d
```

### Start Specific Services

```bash
docker compose up -d api postgres redis
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

## Service Dependencies

```yaml
api:
  depends_on:
    - pgbouncer
    - migrations
    - collectstatic
    - celery-worker

migrations:
  depends_on:
    - pgbouncer

celery-worker:
  depends_on:
    - pgbouncer
    - migrations
    - redis

pgbouncer:
  depends_on:
    postgres:
      condition: service_healthy
```

## Health Checks

### PostgreSQL

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

### PgBouncer

```yaml
pgbouncer:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -p 5432"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 5s
```

### MinIO

```yaml
minio:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 2s
    timeout: 10s
    retries: 5
```

## Volumes

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
```

## Local Development Overrides

`docker-compose.local.yaml` adds development features:

```yaml
services:
  api:
    volumes:
      - ./src:/app/src:ro
    command:
      - python
      - manage.py
      - runserver
      - 0.0.0.0:8000

  celery-worker:
    volumes:
      - ./src:/app/src:ro
    command:
      - watchmedo
      - auto-restart
      - --directory=/app/src
      - --pattern=*.py
      - --recursive
      - --
      - celery
      - --app=delivery.tasks.app
      - worker
      - --loglevel=${LOGGING_LEVEL:-INFO}

  postgres:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"
```

## Using Local Configuration

```bash
# Set in .env
COMPOSE_FILE=docker-compose.yaml:docker-compose.local.yaml

# Or explicitly
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up -d
```

## Scaling

### Multiple Workers

```bash
docker compose up -d --scale celery-worker=4
```

### API Replicas

```bash
docker compose up -d --scale api=3
```

!!! note "Load Balancer Required"
    For multiple API replicas, add a load balancer (nginx, traefik).

## Commands

### Run Migrations

```bash
docker compose exec api python manage.py migrate
```

### Create Superuser

```bash
docker compose exec api python manage.py createsuperuser
```

### Django Shell

```bash
docker compose exec api python manage.py shell
```

### Database Shell

```bash
docker compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

## Stopping Services

```bash
# Stop all
docker compose down

# Stop and remove volumes
docker compose down -v

# Stop specific service
docker compose stop api
```

## Related Topics

- [Production Checklist](production-checklist.md) — Deployment checklist
- [Docker Services Reference](../reference/docker-services.md) — Detailed configuration
- [Environment Variables](../configuration/environment-variables.md) — All settings
