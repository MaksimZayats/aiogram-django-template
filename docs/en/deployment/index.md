# Deployment

Deploy your application to production.

## Overview

The template includes Docker Compose configuration for production deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Load Balancer                       │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐    ┌───▼───┐    ┌────▼────┐
     │   API   │    │  Bot  │    │ Worker  │
     │ (HTTP)  │    │(Tele) │    │(Celery) │
     └────┬────┘    └───┬───┘    └────┬────┘
          │             │             │
          └─────────────┼─────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
    ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
    │PgBouncer│   │  Redis  │   │  MinIO  │
    └────┬────┘   └─────────┘   └─────────┘
         │
    ┌────▼────┐
    │ Postgres│
    └─────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Docker Compose**

    ---

    Container orchestration and service configuration.

    [:octicons-arrow-right-24: Learn More](docker-compose.md)

-   **Production Checklist**

    ---

    Complete checklist for production deployment.

    [:octicons-arrow-right-24: Learn More](production-checklist.md)

-   **CI/CD**

    ---

    Continuous integration and deployment.

    [:octicons-arrow-right-24: Learn More](ci-cd.md)

</div>

## Quick Deploy

### 1. Configure Environment

Create `.env` with production values:

```bash
ENVIRONMENT=production
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<generate-secure-key>
JWT_SECRET_KEY=<generate-secure-key>
# ... other settings
```

### 2. Build and Start

```bash
docker compose build
docker compose up -d
```

### 3. Run Migrations

```bash
docker compose exec api python manage.py migrate
```

### 4. Verify

```bash
curl http://localhost:8009/v1/health
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8009 | HTTP API (Gunicorn) |
| Bot | — | Telegram bot (polling) |
| Celery Worker | — | Background tasks |
| Celery Beat | — | Task scheduler |
| PgBouncer | — | Connection pool |
| PostgreSQL | — | Database |
| Redis | — | Cache/Broker |
| MinIO | 9000, 9001 | Object storage |

## Related Topics

- [Environment Variables](../configuration/environment-variables.md) — All settings
- [Production Configuration](../configuration/production.md) — Security settings
