# Quick Start

Get the Modern API Template running in 5 minutes.

## 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template

# Install dependencies with uv
uv sync --locked --all-extras --dev
```

## 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env
```

The `.env.example` file contains sensible defaults for local development. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_DEBUG` | `true` | Enable debug mode |
| `DJANGO_SECRET_KEY` | Generated | Django secret key |
| `DATABASE_URL` | `postgres://...` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |

## 3. Start Infrastructure

```bash
# Start PostgreSQL, Redis, and MinIO
docker compose up -d postgres redis minio

# Create MinIO buckets, run migrations, collect static files
docker compose up minio-create-buckets migrations collectstatic
```

!!! tip "What's Running"
    - **PostgreSQL** on port 5432 - Main database
    - **Redis** on port 6379 - Cache and Celery broker
    - **MinIO** on port 9000 - S3-compatible storage (admin UI on 9001)

## 4. Run the Application

Open two terminal windows:

=== "Terminal 1: HTTP API"

    ```bash
    make dev
    ```

    The API will be available at [http://localhost:8000](http://localhost:8000)

=== "Terminal 2: Celery Worker"

    ```bash
    make celery-dev
    ```

    The worker will process background tasks

## 5. Verify It Works

### Check the Health Endpoint

```bash
curl http://localhost:8000/v1/health
```

Expected response:

```json
{"status": "ok"}
```

### Browse the API Documentation

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to see the interactive OpenAPI documentation.

### Access Django Admin

Open [http://localhost:8000/admin](http://localhost:8000/admin) (requires creating a superuser first):

```bash
uv run python src/manage.py createsuperuser
```

## What's Next?

Now that you have the application running:

1. **Understand the structure** - Read [Project Structure](project-structure.md)
2. **Build a feature** - Follow the [Tutorial](../tutorial/index.md)
3. **Learn the patterns** - Explore the [Concepts](../concepts/index.md)

## Troubleshooting

### Port Already in Use

```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>
```

### Database Connection Failed

Ensure PostgreSQL is running:

```bash
docker compose ps postgres
# Should show "running"
```

### Redis Connection Failed

Ensure Redis is running:

```bash
docker compose ps redis
# Should show "running"
```

### Migrations Not Applied

Run migrations manually:

```bash
make migrate
```
