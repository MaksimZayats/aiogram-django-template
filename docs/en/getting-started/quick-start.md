# Quick Start

Get Fast Django running locally in under 5 minutes.

## Prerequisites

Ensure you have installed:

- Python 3.14 or higher
- Docker and Docker Compose
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

## Step 1: Clone the Repository

```bash
git clone https://github.com/MaksimZayats/fast-django.git
cd fast-django
```

## Step 2: Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

The `.env.example` file contains sensible defaults for local development. You can customize these values later as needed.

!!! note "Environment Variables"
    The `.env` file includes the `COMPOSE_FILE` setting that combines the base Docker Compose configuration with local development overrides. This enables features like hot-reload for development.

## Step 3: Start Infrastructure Services

Start PostgreSQL, Redis, and MinIO:

```bash
docker compose up -d postgres redis minio
```

!!! info "What Each Service Does"
    - **PostgreSQL** - Primary database for storing application data
    - **Redis** - Caching layer and Celery message broker
    - **MinIO** - S3-compatible object storage for static files and media

## Step 4: Initialize the Database

Create MinIO buckets, run database migrations, and collect static files:

```bash
docker compose up minio-create-buckets migrations collectstatic
```

This runs one-time setup tasks:

1. Creates `public` and `protected` buckets in MinIO
2. Applies Django database migrations
3. Collects static files to MinIO

## Step 5: Install Python Dependencies

```bash
uv sync --locked --all-extras --dev
```

This installs all dependencies from the lockfile, including development tools.

## Step 6: Run the Development Server

```bash
make dev
```

!!! success "You're Ready!"
    The API is now running at [http://localhost:8000](http://localhost:8000)

## Explore the API

Open the interactive API documentation:

- **Swagger UI**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

The documentation is auto-generated from your code and includes:

- All available endpoints
- Request/response schemas
- Authentication requirements
- Try-it-out functionality

## Running Additional Services

### Celery Worker (Background Tasks)

In a separate terminal:

```bash
make celery-dev
```

### Celery Beat (Scheduled Tasks)

In another terminal:

```bash
make celery-beat-dev
```

## Verify Everything Works

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{"status": "ok"}
```

### Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePass123!"
  }'
```

## Next Steps

Now that the project is running:

1. **[Project Structure](project-structure.md)** - Understand how the codebase is organized
2. **[Development Environment](development-environment.md)** - Configure your IDE for the best experience
3. **[Tutorial: Build a Todo List](../tutorial/index.md)** - Learn by building a complete feature
