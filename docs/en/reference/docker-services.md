# Docker Services

Reference for Docker Compose services and their configuration.

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Redis cache and message broker |
| `minio` | 9000, 9001 | S3-compatible object storage |
| `minio-create-buckets` | - | One-time bucket creation |
| `migrations` | - | One-time database migration |
| `collectstatic` | - | One-time static file collection |

## PostgreSQL

### Configuration

```yaml
postgres:
  image: postgres:16-alpine
  ports:
    - "5432:5432"
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: app
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

### Connection

```bash
# Local connection
psql postgres://postgres:postgres@localhost:5432/app

# From another container
DATABASE_URL=postgres://postgres:postgres@postgres:5432/app
```

### Persistence

Data persists in the `postgres_data` volume. To reset:

```bash
docker compose down -v postgres
docker compose up -d postgres
```

## Redis

### Configuration

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

### Connection

```bash
# CLI access
redis-cli -h localhost -p 6379

# Connection URL
REDIS_URL=redis://localhost:6379
```

### Use Cases

- **Cache backend** - Django cache
- **Celery broker** - Task queue
- **Celery result backend** - Task results
- **Rate limiting** - Throttle storage

## MinIO

S3-compatible object storage for local development.

### Configuration

```yaml
minio:
  image: minio/minio
  ports:
    - "9000:9000"   # API
    - "9001:9001"   # Console
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  command: server /data --console-address ":9001"
  volumes:
    - minio_data:/data
```

### Access

| Interface | URL |
|-----------|-----|
| API | http://localhost:9000 |
| Console | http://localhost:9001 |

Console credentials: `minioadmin` / `minioadmin`

### Environment Variables

```bash
AWS_S3_ENDPOINT_URL=http://localhost:9000
AWS_S3_ACCESS_KEY_ID=minioadmin
AWS_S3_SECRET_ACCESS_KEY=minioadmin
AWS_S3_BUCKET_NAME=app-bucket
```

## One-Time Services

These services run once and exit.

### `minio-create-buckets`

Creates required S3 buckets.

```yaml
minio-create-buckets:
  image: minio/mc
  depends_on:
    - minio
  entrypoint: >
    /bin/sh -c "
    mc alias set myminio http://minio:9000 minioadmin minioadmin;
    mc mb myminio/app-bucket --ignore-existing;
    mc anonymous set public myminio/app-bucket;
    "
```

Run manually:

```bash
docker compose up minio-create-buckets
```

### `migrations`

Applies database migrations.

```yaml
migrations:
  build: .
  command: python src/manage.py migrate
  depends_on:
    - postgres
  environment:
    DATABASE_URL: postgres://postgres:postgres@postgres:5432/app
```

Run manually:

```bash
docker compose up migrations
```

### `collectstatic`

Collects static files.

```yaml
collectstatic:
  build: .
  command: python src/manage.py collectstatic --noinput
  volumes:
    - static_files:/app/static
```

Run manually:

```bash
docker compose up collectstatic
```

## Common Commands

### Start Infrastructure

```bash
# Start persistent services
docker compose up -d postgres redis minio

# Run one-time setup
docker compose up minio-create-buckets migrations collectstatic
```

### Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (reset data)
docker compose down -v
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f postgres
```

### Check Status

```bash
docker compose ps
```

### Execute Commands

```bash
# PostgreSQL shell
docker compose exec postgres psql -U postgres -d app

# Redis CLI
docker compose exec redis redis-cli
```

## Health Checks

### PostgreSQL

```bash
docker compose exec postgres pg_isready -U postgres
```

### Redis

```bash
docker compose exec redis redis-cli ping
```

### MinIO

```bash
curl -f http://localhost:9000/minio/health/live
```

## Production Considerations

For production, consider:

### PostgreSQL

- Use managed database (RDS, Cloud SQL)
- Enable SSL connections
- Set up replication
- Configure backups

### Redis

- Use managed Redis (ElastiCache, Redis Cloud)
- Enable persistence
- Configure memory limits
- Set up sentinels for HA

### MinIO

- Use production S3 or managed storage
- Configure proper bucket policies
- Enable versioning
- Set up lifecycle rules

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs postgres

# Check container status
docker compose ps -a
```

### Port Already in Use

```bash
# Find process using port
lsof -i :5432

# Kill process or change port in docker-compose.yml
```

### Database Connection Refused

```bash
# Ensure PostgreSQL is running
docker compose ps postgres

# Check health
docker compose exec postgres pg_isready -U postgres
```

### Redis Connection Refused

```bash
# Ensure Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping
```

### Reset Everything

```bash
# Stop and remove all containers and volumes
docker compose down -v --remove-orphans

# Start fresh
docker compose up -d postgres redis minio
docker compose up minio-create-buckets migrations collectstatic
```

## Related

- [Environment Variables](environment-variables.md) - Configuration options
- [Makefile Commands](makefile.md) - Development commands
- [Quick Start](../getting-started/quick-start.md) - Getting started
