# How-To Guides

Step-by-step guides for common tasks.

## In This Section

| Guide | Description |
|-------|-------------|
| [Add a New Domain](add-new-domain.md) | Complete checklist for adding a new feature domain |
| [Custom Exception Handling](custom-exception-handling.md) | Map domain exceptions to HTTP responses |
| [Override IoC in Tests](override-ioc-in-tests.md) | Mock dependencies for testing |
| [Add Celery Task](add-celery-task.md) | Quick reference for background tasks |
| [Secure Endpoints](secure-endpoints.md) | JWT authentication and rate limiting |
| [Configure Observability](configure-observability.md) | Set up Logfire or alternative backends |

## Quick Reference

### Adding a New Feature

1. Create model in `core/<domain>/models.py`
2. Create service in `core/<domain>/services.py`
3. Register service in `ioc/registries/core.py`
4. Create controller in `delivery/http/<domain>/controllers.py`
5. Register controller in `ioc/registries/delivery.py`
6. Update factory in `delivery/http/factories.py`

See [Add a New Domain](add-new-domain.md) for the full guide.

### Common Commands

```bash
# Development
make dev              # Start HTTP server
make celery-dev       # Start Celery worker
make migrate          # Apply migrations
make makemigrations   # Create migrations

# Quality
make format           # Format code
make lint             # Run linters
make test             # Run tests

# Docker
docker compose up -d postgres redis  # Start infrastructure
docker compose down                  # Stop containers
```
