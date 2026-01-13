# Production Configuration

Security settings and best practices for production deployment.

## Critical Settings

### Django Secret Key

Generate a secure secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```bash
DJANGO_SECRET_KEY=your-generated-secret-key
```

!!! danger "Never commit secrets"
    Never commit production secrets to version control.

### Debug Mode

Always disable debug in production:

```bash
DJANGO_DEBUG=false
```

### Environment

Set the environment explicitly:

```bash
ENVIRONMENT=production
```

This affects:

- API documentation access (staff-only in production)
- Logging configuration
- Error handling verbosity

## Host Configuration

### Allowed Hosts

Specify your domain(s):

```bash
ALLOWED_HOSTS='["api.example.com", "example.com"]'
```

### CSRF Trusted Origins

Include your frontend domain(s):

```bash
CSRF_TRUSTED_ORIGINS='["https://example.com", "https://app.example.com"]'
```

## JWT Configuration

### Secret Key

Generate a secure JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

```bash
JWT_SECRET_KEY=your-jwt-secret
```

### Token Expiration

Set appropriate expiration times:

```bash
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15  # Short-lived access tokens
REFRESH_TOKEN_TTL_DAYS=7            # Shorter for production
```

## Database

### Connection URL

Use a secure connection string:

```bash
DATABASE_URL=postgres://user:password@host:5432/database?sslmode=require
```

### Connection Pooling

PgBouncer is included in Docker Compose for connection pooling:

```yaml
pgbouncer:
  environment:
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 200
    DEFAULT_POOL_SIZE: 25
```

## Redis

### Secure Connection

Use authentication:

```bash
REDIS_URL=redis://default:password@host:6379/0
```

For TLS:

```bash
REDIS_URL=rediss://default:password@host:6379/0
```

## Observability

### Enable Logfire

For production monitoring:

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your-logfire-token
```

### Logging Level

Use appropriate level:

```bash
LOGGING_LEVEL=INFO  # Not DEBUG in production
```

## Complete Production .env

```bash
# Environment
ENVIRONMENT=production

# Django
DJANGO_SECRET_KEY=your-super-secure-secret-key
DJANGO_DEBUG=false

# HTTP
ALLOWED_HOSTS='["api.example.com"]'
CSRF_TRUSTED_ORIGINS='["https://example.com"]'

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Database
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure-db-password
POSTGRES_DB=app_production
DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@pgbouncer:5432/${POSTGRES_DB}

# Redis
REDIS_PASSWORD=secure-redis-password
REDIS_URL=redis://default:${REDIS_PASSWORD}@redis:6379/0

# S3 Storage
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com
AWS_S3_ACCESS_KEY_ID=your-access-key
AWS_S3_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_PROTECTED_BUCKET_NAME=app-protected
AWS_S3_PUBLIC_BUCKET_NAME=app-public

# Observability
LOGGING_LEVEL=INFO
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your-logfire-token

# Telegram Bot (if used)
TELEGRAM_BOT_TOKEN=your-bot-token
```

## Security Checklist

### Before Deployment

- [ ] Generated unique `DJANGO_SECRET_KEY`
- [ ] Generated unique `JWT_SECRET_KEY`
- [ ] Set `DJANGO_DEBUG=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configured `ALLOWED_HOSTS`
- [ ] Configured `CSRF_TRUSTED_ORIGINS`
- [ ] Set strong database password
- [ ] Set strong Redis password
- [ ] Enabled HTTPS/TLS
- [ ] Set up Logfire monitoring

### Infrastructure

- [ ] Database backups configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Rate limiting enabled
- [ ] Health checks configured

## Django Security Settings

Additional Django security settings (add to a custom settings class if needed):

```python
# In production, consider adding:
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Gunicorn Configuration

The production Docker Compose uses Gunicorn:

```yaml
api:
  command:
    - gunicorn
    - delivery.http.app:wsgi
    - --workers=4
    - --bind=0.0.0.0
    - --timeout=120
```

Adjust workers based on CPU cores:

```
workers = (2 × CPU cores) + 1
```

## Related Topics

- [Docker Compose Deployment](../deployment/docker-compose.md) — Deployment guide
- [Production Checklist](../deployment/production-checklist.md) — Full checklist
- [Logfire](../observability/logfire.md) — Production monitoring
