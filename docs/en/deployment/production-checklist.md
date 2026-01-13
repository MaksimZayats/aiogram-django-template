# Production Checklist

Complete checklist before deploying to production.

## Security

### Secrets

- [ ] Generated unique `DJANGO_SECRET_KEY`
- [ ] Generated unique `JWT_SECRET_KEY`
- [ ] Set strong `POSTGRES_PASSWORD`
- [ ] Set strong `REDIS_PASSWORD`
- [ ] Set strong `AWS_S3_SECRET_ACCESS_KEY`
- [ ] Never committed secrets to version control
- [ ] Using environment variables or secret manager

### Django Settings

- [ ] Set `DJANGO_DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configured `ALLOWED_HOSTS` correctly
- [ ] Configured `CSRF_TRUSTED_ORIGINS` correctly

### Network

- [ ] HTTPS/TLS enabled
- [ ] Firewall rules configured
- [ ] Internal services not exposed publicly
- [ ] Rate limiting configured

### Authentication

- [ ] JWT tokens have appropriate TTL
- [ ] Refresh token rotation enabled
- [ ] Password validation enabled

## Database

### PostgreSQL

- [ ] Using PgBouncer for connection pooling
- [ ] Database backups configured
- [ ] Point-in-time recovery enabled
- [ ] Connection limits set appropriately
- [ ] SSL/TLS for database connections

### Migrations

- [ ] All migrations applied
- [ ] No pending migrations

## Infrastructure

### Docker

- [ ] Images built without development dependencies
- [ ] Health checks configured
- [ ] Resource limits set
- [ ] Restart policies configured

### Gunicorn

- [ ] Worker count based on CPU cores
- [ ] Timeout configured appropriately
- [ ] Access logging enabled

### Celery

- [ ] Worker concurrency set appropriately
- [ ] Only one Beat instance running
- [ ] Result backend configured
- [ ] Task timeouts set

### Redis

- [ ] Authentication enabled
- [ ] Memory limits configured
- [ ] Persistence configured (if needed)

### MinIO/S3

- [ ] Bucket policies configured
- [ ] Access keys rotated
- [ ] CORS configured (if needed)

## Observability

### Logging

- [ ] Log level set to INFO or higher
- [ ] Log rotation configured
- [ ] Log aggregation set up

### Monitoring

- [ ] Logfire enabled and configured
- [ ] Health endpoints accessible
- [ ] Alerts configured

### Tracing

- [ ] Sensitive data scrubbing enabled
- [ ] Service names configured correctly

## Application

### Configuration

- [ ] Environment variables set correctly
- [ ] No development defaults in production
- [ ] Static files collected

### Performance

- [ ] Database indexes created
- [ ] Caching configured
- [ ] Query optimization done

## Operations

### Backups

- [ ] Database backup schedule configured
- [ ] Backup restoration tested
- [ ] Backup retention policy set

### Updates

- [ ] Zero-downtime deployment strategy
- [ ] Rollback procedure documented
- [ ] Database migration strategy

### Documentation

- [ ] Runbook created
- [ ] Incident response plan
- [ ] Contact information updated

## Pre-Deploy Commands

```bash
# 1. Verify environment
cat .env | grep -E "^(ENVIRONMENT|DJANGO_DEBUG)="

# 2. Build images
docker compose build

# 3. Run migrations
docker compose run --rm api python manage.py migrate --check

# 4. Collect static files
docker compose run --rm api python manage.py collectstatic --noinput

# 5. Run tests
docker compose run --rm api pytest tests/

# 6. Check security
docker compose run --rm api python manage.py check --deploy
```

## Post-Deploy Verification

```bash
# 1. Check services are running
docker compose ps

# 2. Check health endpoint
curl -f https://your-domain.com/v1/health

# 3. Check logs for errors
docker compose logs --tail=100 api | grep -i error

# 4. Verify database connectivity
docker compose exec api python manage.py dbshell -c "SELECT 1"

# 5. Test a protected endpoint
curl -X POST https://your-domain.com/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'
```

## Quick Reference

### Generate Secrets

```bash
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generic secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Check Settings

```bash
docker compose exec api python manage.py diffsettings
```

### Security Check

```bash
docker compose exec api python manage.py check --deploy
```

## Related Topics

- [Production Configuration](../configuration/production.md) — Security settings
- [Docker Compose](docker-compose.md) — Container configuration
- [Environment Variables](../configuration/environment-variables.md) — All settings
