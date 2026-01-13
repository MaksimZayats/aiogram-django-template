# Instrumented Libraries

Auto-instrumented libraries for distributed tracing.

## Overview

Logfire automatically instruments common libraries:

```python
# src/infrastructure/otel/logfire.py

def _instrument_libraries() -> None:
    logfire.instrument_django(
        excluded_urls=".*/v1/health",
        is_sql_commentor_enabled=True,
    )
    logfire.instrument_celery(propagate_trace_context=True)
    logfire.instrument_requests()
    logfire.instrument_psycopg(
        enable_commenter=True,
        commenter_options=CommenterOptions(
            db_driver=True,
            dbapi_level=True,
        ),
    )
    logfire.instrument_httpx()
    logfire.instrument_redis()
    logfire.instrument_pydantic()
```

## Django Instrumentation

```python
logfire.instrument_django(
    excluded_urls=".*/v1/health",
    is_sql_commentor_enabled=True,
)
```

### Features

- HTTP request/response tracing
- URL routing information
- Request headers and body
- Response status and timing

### Excluded URLs

Health check endpoints are excluded to reduce noise:

```python
excluded_urls=".*/v1/health"
```

### SQL Commenter

Adds trace context to SQL queries:

```sql
SELECT * FROM users WHERE id = 1
/* traceparent='00-abc123-def456-01' */
```

## Celery Instrumentation

```python
logfire.instrument_celery(propagate_trace_context=True)
```

### Features

- Task execution tracing
- Task arguments and results
- Retry tracking
- Queue information

### Context Propagation

`propagate_trace_context=True` links task traces to parent spans:

```
[HTTP Request] → [Task Created] → [Worker: Task Executed]
```

## PostgreSQL (psycopg) Instrumentation

```python
logfire.instrument_psycopg(
    enable_commenter=True,
    commenter_options=CommenterOptions(
        db_driver=True,
        dbapi_level=True,
    ),
)
```

### Features

- Query execution timing
- Query text (sanitized)
- Connection information
- Error tracking

### SQL Comments

Adds metadata to queries:

```sql
SELECT * FROM users
/* db_driver='psycopg2', dbapi_level='2.0' */
```

## Requests Instrumentation

```python
logfire.instrument_requests()
```

### Features

- Outbound HTTP request tracing
- URL, method, headers
- Response status and timing
- Error tracking

### Example Trace

```
[Your API] → [External API] GET https://api.example.com/data
└── 200 OK (350ms)
```

## HTTPX Instrumentation

```python
logfire.instrument_httpx()
```

### Features

- Async HTTP client tracing
- Same capabilities as requests
- Connection pooling visibility

## Redis Instrumentation

```python
logfire.instrument_redis()
```

### Features

- Redis command tracing
- Key operations
- Timing information
- Error tracking

### Example Trace

```
[Redis] GET cache:user:123 → "John Doe" (2ms)
[Redis] SET cache:user:123 "John Doe" EX 3600 (1ms)
```

## Pydantic Instrumentation

```python
logfire.instrument_pydantic()
```

### Features

- Validation timing
- Validation errors
- Model serialization

## What Gets Traced

### Automatic Traces

| Library | Traced Operations |
|---------|-------------------|
| Django | HTTP requests, responses |
| Celery | Task execution |
| psycopg | SQL queries |
| requests | HTTP client calls |
| httpx | Async HTTP calls |
| Redis | Cache operations |
| Pydantic | Validation |

### Sample Trace

```
[HTTP] POST /v1/users/
├── [Pydantic] Validate CreateUserSchema
├── [DB] SELECT * FROM users WHERE email = 'test@example.com'
├── [DB] INSERT INTO users (email, username, ...) VALUES (...)
├── [Redis] SET session:abc123 "..." EX 86400
└── [HTTP] 200 OK (45ms)
```

## Custom Instrumentation

Add manual spans for application-specific operations:

```python
import logfire

with logfire.span("custom_operation"):
    # Your code here
    pass
```

## Disabling Instrumentation

To disable specific instrumentation, don't call it:

```python
def _instrument_libraries() -> None:
    logfire.instrument_django(...)
    logfire.instrument_celery(...)
    # logfire.instrument_redis()  # Disabled
```

## Performance Impact

Instrumentation adds minimal overhead:

- ~1-5ms per request for basic tracing
- SQL commenter adds ~0.1ms per query
- Background span export (non-blocking)

## Related Topics

- [Logfire](logfire.md) — Logfire setup
- [Sensitive Data Scrubbing](scrubbing.md) — Data protection
- [Logging](logging.md) — Console logging
