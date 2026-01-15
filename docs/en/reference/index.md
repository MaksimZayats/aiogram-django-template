# Reference

Technical reference documentation for configuration and tooling.

## In This Section

| Reference | Description |
|-----------|-------------|
| [Environment Variables](environment-variables.md) | Complete list of configuration options |
| [Makefile Commands](makefile.md) | Development command reference |
| [Docker Services](docker-services.md) | Container configuration details |

## Quick Reference

### Required Environment Variables

These must be set in production:

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key (generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `JWT_SECRET_KEY` | JWT signing key (generate separately) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |

### Common Commands

```bash
# Development
make dev              # Start HTTP server
make celery-dev       # Start Celery worker
make migrate          # Apply migrations
make test             # Run tests

# Code Quality
make format           # Format code
make lint             # Run linters
```

### Docker Services

```bash
# Start infrastructure
docker compose up -d postgres redis minio

# Run setup tasks
docker compose up minio-create-buckets migrations collectstatic

# Stop everything
docker compose down
```
