# Quick Start

Get the application running in 5 minutes.

## 1. Clone the Repository

```bash
git clone https://github.com/MaksimZayats/modern-django-template.git
cd modern-django-template
```

## 2. Install Dependencies

```bash
uv sync --locked --all-extras --dev
```

This installs all dependencies including development tools (ruff, mypy, pytest).

## 3. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

The default configuration works for local development. Key variables:

```bash
DJANGO_SECRET_KEY=example-django-secret-key
JWT_SECRET_KEY=example-jwt-secret
DATABASE_URL="postgres://postgres:example-postgres-password@localhost:5432/postgres"
REDIS_URL="redis://default:example-redis-password@localhost:6379/0"
```

!!! warning "Production"
    Generate secure secrets for production. Never use example values.

## 4. Start Infrastructure

Start PostgreSQL, Redis, and MinIO:

```bash
docker compose -f docker-compose.yaml -f docker-compose.local.yaml up -d
```

Verify services are running:

```bash
docker compose ps
```

## 5. Run Migrations

```bash
make migrate
```

## 6. Start the Development Server

```bash
make dev
```

The API is now available at `http://localhost:8000`.

## 7. Verify It Works

### Check the Health Endpoint

```bash
curl http://localhost:8000/v1/health
```

Expected response:

```json
{"status": "ok"}
```

### Browse the API Documentation

Open `http://localhost:8000/docs` in your browser to see the interactive OpenAPI documentation.

## Optional: Start Celery Worker

In a separate terminal:

```bash
make celery-dev
```

## Optional: Start Telegram Bot

1. Get a bot token from [@BotFather](https://t.me/BotFather)
2. Add to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your-bot-token
   ```
3. Start the bot:
   ```bash
   make bot-dev
   ```

## Next Steps

- [Development Environment](development-environment.md) — Complete IDE setup
- [Project Structure](project-structure.md) — Understand the codebase
- [Your First API Endpoint](../tutorials/first-api-endpoint.md) — Add a new endpoint
