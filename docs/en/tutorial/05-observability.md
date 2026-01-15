# Step 5: Observability

In this step, you'll configure Logfire for observability - tracing, logging, and monitoring of your application.

## No Code Changes Required

This step is configuration-only. The template already includes Logfire integration.

## What is Logfire?

[Logfire](https://logfire.pydantic.dev/) is an OpenTelemetry-based observability platform by Pydantic. It provides:

- **Distributed tracing** - Track requests across services
- **Structured logging** - Queryable log data
- **Metrics** - Performance monitoring
- **Error tracking** - Exception reporting

**OpenTelemetry-compatible** - Logfire uses the OpenTelemetry standard, so you can switch to other backends (Jaeger, Honeycomb, Datadog) if needed.

## Getting a Logfire Token

1. Go to [https://logfire.pydantic.dev/](https://logfire.pydantic.dev/)
2. Create an account (free tier available)
3. Create a new project
4. Go to Project Settings → Write Tokens
5. Generate a new write token

## Configure Environment Variables

Add these to your `.env` file:

```bash
# Enable Logfire
LOGFIRE_ENABLED=true

# Your write token from Logfire dashboard
LOGFIRE_TOKEN=your_write_token_here
```

## What Gets Instrumented Automatically

Once enabled, Logfire automatically instruments:

| Component | What's Captured |
|-----------|-----------------|
| **Django** | Request/response, middleware, views |
| **Celery** | Task execution, retries, failures |
| **PostgreSQL** | Queries with trace context in SQL comments |
| **Redis** | Cache operations, Celery broker calls |
| **HTTP clients** | requests, httpx, aiohttp |
| **Pydantic** | Validation errors |

### Excluded Endpoints

Health check endpoints (`/v1/health`) are excluded from tracing to reduce noise.

## Trace Context Propagation

Traces automatically propagate across:

- HTTP API → Service → Database
- HTTP API → Celery Task → Database
- Celery Task → HTTP Client → External API

This gives you a complete picture of request flow.

## SQL Query Comments

PostgreSQL queries include trace context in SQL comments:

```sql
/* traceparent=00-abc123-def456-01 */
SELECT * FROM core_todo WHERE user_id = 1;
```

This allows correlating slow queries with specific requests.

## Scrubbing Sensitive Data

Logfire automatically scrubs common sensitive patterns:

- `password`
- `secret`
- `token`
- `api_key`
- `authorization`

The template adds custom patterns:

- `access_token`
- `refresh_token`

## Viewing Traces

After enabling Logfire:

1. Make some requests to your API:
   ```bash
   curl http://localhost:8000/v1/health
   curl -X POST http://localhost:8000/v1/users/me/token \
     -H "Content-Type: application/json" \
     -d '{"username": "testuser", "password": "testpass"}'
   ```

2. Open the Logfire dashboard
3. View traces in the Explore tab

You'll see:

- Request duration breakdown
- Database query timing
- Error stack traces
- Cross-service correlation

## Using a Different Backend

Since Logfire uses OpenTelemetry, you can switch backends:

### Jaeger

```python
# Set OTLP endpoint instead of Logfire token
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Honeycomb

```python
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=your-api-key
```

See [Configure Observability](../how-to/configure-observability.md) for detailed instructions.

## Best Practices

### 1. Use Structured Logging

```python
import logfire

# Good - structured data
logfire.info("Todo created", todo_id=todo.id, user_id=user.id)

# Bad - string interpolation
logfire.info(f"Todo {todo.id} created by {user.id}")
```

### 2. Add Custom Spans

```python
import logfire

with logfire.span("process_todos"):
    # Complex operation
    for todo in todos:
        with logfire.span("process_todo", todo_id=todo.id):
            process_todo(todo)
```

### 3. Include Context in Errors

```python
try:
    result = process_data(data)
except ValueError as e:
    logfire.error("Processing failed", error=str(e), data_id=data.id)
    raise
```

## What You've Learned

In this step, you:

1. Understood what Logfire provides
2. Configured environment variables for observability
3. Learned what gets automatically instrumented
4. Saw how to view traces
5. Understood options for alternative backends

## Next Step

In [Step 6: Testing](06-testing.md), you'll write integration tests for your Todo API and Celery task.
