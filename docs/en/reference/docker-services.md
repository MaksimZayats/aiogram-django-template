# Docker Services Reference

Docker Compose service configuration details.

## Application Services

### API (HTTP)

```yaml
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
  depends_on:
    - pgbouncer
    - migrations
    - collectstatic
    - celery-worker
  restart: always
```

| Setting | Value | Description |
|---------|-------|-------------|
| Port | 8009 (external), 8000 (internal) | HTTP port |
| Workers | 4 | Gunicorn worker processes |
| Timeout | 120s | Request timeout |

### Celery Worker

```yaml
celery-worker:
  image: base:local
  command:
    - celery
    - --app=delivery.tasks.app
    - worker
    - --loglevel=${LOGGING_LEVEL:-INFO}
    - --concurrency=4
  depends_on:
    - pgbouncer
    - migrations
    - redis
  restart: always
```

| Setting | Value | Description |
|---------|-------|-------------|
| Concurrency | 4 | Worker processes |
| Log Level | INFO (default) | Celery log level |

### Celery Beat

```yaml
celery-beat:
  image: base:local
  command:
    - celery
    - --app=delivery.tasks.app
    - beat
    - --loglevel=${LOGGING_LEVEL:-INFO}
  depends_on:
    - pgbouncer
    - migrations
    - redis
  restart: always
```

!!! warning "Single Instance"
    Only run one Beat instance to avoid duplicate scheduled tasks.

### Telegram Bot

```yaml
bot:
  image: base:local
  command: python -m delivery.bot
  depends_on:
    - pgbouncer
    - migrations
  restart: always
```

## Infrastructure Services

### PostgreSQL

```yaml
postgres:
  image: postgres:18-alpine
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    POSTGRES_INITDB_ARGS: --auth-host=scram-sha-256
  volumes:
    - postgres_data:/var/lib/postgresql
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 10s
```

| Setting | Value | Description |
|---------|-------|-------------|
| Image | postgres:18-alpine | PostgreSQL 18 |
| Auth | scram-sha-256 | Secure authentication |
| Volume | postgres_data | Persistent storage |

### PgBouncer

```yaml
pgbouncer:
  image: edoburu/pgbouncer:latest
  environment:
    DATABASE_URL: postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 200
    DEFAULT_POOL_SIZE: 25
    MIN_POOL_SIZE: 5
    RESERVE_POOL_SIZE: 5
    RESERVE_POOL_TIMEOUT: 3
    SERVER_RESET_QUERY: DISCARD ALL
    SERVER_LIFETIME: 3600
    SERVER_IDLE_TIMEOUT: 600
    LOG_CONNECTIONS: 0
    LOG_DISCONNECTIONS: 0
    LOG_POOLER_ERRORS: 1
    AUTH_TYPE: scram-sha-256
  depends_on:
    postgres:
      condition: service_healthy
```

| Setting | Value | Description |
|---------|-------|-------------|
| Pool Mode | transaction | Connection pooling mode |
| Max Clients | 200 | Maximum client connections |
| Default Pool | 25 | Default pool size per user/db |
| Server Lifetime | 3600s | Connection max age |

### Redis

```yaml
redis:
  image: redis:latest
  volumes:
    - redis_data:/data
```

| Setting | Value | Description |
|---------|-------|-------------|
| Image | redis:latest | Latest Redis |
| Volume | redis_data | Persistent storage |

### MinIO

```yaml
minio:
  image: minio/minio:latest
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: ${AWS_S3_ACCESS_KEY_ID}
    MINIO_ROOT_PASSWORD: ${AWS_S3_SECRET_ACCESS_KEY}
  volumes:
    - minio_data:/data
  command: server /data --console-address ":9001"
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 2s
    timeout: 10s
    retries: 5
```

| Setting | Value | Description |
|---------|-------|-------------|
| API Port | 9000 | S3 API endpoint |
| Console Port | 9001 | Web UI |
| Volume | minio_data | Persistent storage |

### MinIO Bucket Setup

```yaml
minio-create-buckets:
  image: minio/mc
  depends_on:
    minio:
      condition: service_healthy
  entrypoint: >
    /bin/sh -c "
    /usr/bin/mc alias set my-minio http://minio:9000 ... ;
    /usr/bin/mc mb my-minio/${AWS_S3_PROTECTED_BUCKET_NAME:-protected};
    mc anonymous set none my-minio/${AWS_S3_PROTECTED_BUCKET_NAME:-protected};
    /usr/bin/mc mb my-minio/${AWS_S3_PUBLIC_BUCKET_NAME:-public};
    mc anonymous set public my-minio/${AWS_S3_PUBLIC_BUCKET_NAME:-public};
    exit 0;
    "
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

## Networks

```yaml
networks:
  main:
    driver: bridge
```

All services are on the `main` bridge network for internal communication.

## Local Development Overrides

`docker-compose.local.yaml`:

| Service | Override |
|---------|----------|
| API | Use runserver instead of gunicorn, mount source |
| Celery Worker | Add watchmedo auto-restart |
| PostgreSQL | Expose port 5432 |
| Redis | Expose port 6379 |
| MinIO | Ports already exposed |
