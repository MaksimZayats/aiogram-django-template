# Step 5: Observability

In this step, you will configure observability for your application using Logfire, an OpenTelemetry-based observability platform by Pydantic. This provides distributed tracing, automatic instrumentation, and sensitive data scrubbing.

## What You Will Learn

- What Logfire is and why it matters
- How to obtain a Logfire token
- What gets automatically instrumented
- How sensitive data is scrubbed
- How to swap Logfire for other OpenTelemetry backends

!!! note "No Code Changes Required"
    This step requires only environment configuration. The template already includes full Logfire integration.

---

## What is Logfire?

[Logfire](https://logfire.pydantic.dev/) is an observability platform built by the creators of Pydantic. It provides:

- **Distributed Tracing**: Follow requests across HTTP, Celery tasks, and database queries
- **Automatic Instrumentation**: Zero-config tracing for Django, Celery, PostgreSQL, Redis, and more
- **Pydantic Integration**: See validation errors with full context
- **OpenTelemetry Native**: Uses standard OTEL protocols, making it interchangeable with other backends

---

## Getting a Logfire Token

1. Go to [logfire.pydantic.dev](https://logfire.pydantic.dev/)
2. Create an account or sign in
3. Create a new project (e.g., `my-todo-app`)
4. Navigate to **Settings** > **Write Tokens**
5. Generate a new write token
6. Copy the token for the next step

!!! warning "Keep Your Token Secret"
    Never commit your Logfire token to version control. Use environment variables or a secrets manager.

---

## Environment Configuration

Add these environment variables to your `.env` file:

```bash title=".env"
# Observability
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your_write_token_here
```

| Variable | Description | Default |
|----------|-------------|---------|
| `LOGFIRE_ENABLED` | Enable/disable Logfire instrumentation | `false` |
| `LOGFIRE_TOKEN` | Your Logfire write token | `None` |

!!! tip "Development vs Production"
    You can disable Logfire locally by setting `LOGFIRE_ENABLED=false` to reduce noise during development.

---

## What Gets Instrumented

The template automatically instruments these libraries when Logfire is enabled:

| Library | What is Traced |
|---------|----------------|
| **Django** | HTTP requests, responses, middleware timing |
| **Celery** | Task execution, retries, failures |
| **PostgreSQL (psycopg)** | SQL queries with timing and parameters |
| **Redis** | Cache operations and commands |
| **HTTP Clients (requests, httpx)** | Outbound HTTP calls |
| **Pydantic** | Validation errors with context |

### Example Trace

When a user creates a todo, you will see a trace like:

```
POST /v1/todos/ (45ms)
├── JWT Authentication (2ms)
├── Pydantic Validation (1ms)
├── TodoService.create_todo (38ms)
│   └── INSERT INTO todo_todo... (35ms)
└── Response Serialization (1ms)
```

---

## Sensitive Data Scrubbing

Logfire automatically scrubs sensitive data from traces. The template adds custom patterns for JWT tokens:

```python title="src/infrastructure/otel/logfire.py"
logfire.configure(
    # ...
    scrubbing=ScrubbingOptions(
        extra_patterns=[
            "access_token",
            "refresh_token",
        ],
    ),
)
```

### Built-in Scrubbing Patterns

Logfire scrubs these by default:

- `password`, `passwd`, `pwd`
- `secret`, `api_key`, `apikey`
- `token`, `auth`, `credential`
- `ssn`, `social_security`
- Credit card patterns

### Custom Patterns

Add additional patterns in `src/infrastructure/otel/logfire.py`:

```python
scrubbing=ScrubbingOptions(
    extra_patterns=[
        "access_token",
        "refresh_token",
        "my_custom_secret",  # Add your patterns
    ],
),
```

---

## Viewing Traces

Once configured, traces appear in the Logfire dashboard:

1. Open [logfire.pydantic.dev](https://logfire.pydantic.dev/)
2. Select your project
3. Navigate to **Live** to see real-time traces
4. Use **Explore** to search historical traces

### Useful Queries

| Query | Purpose |
|-------|---------|
| `service.name:http-api` | Filter HTTP API traces |
| `service.name:celery-worker` | Filter Celery worker traces |
| `span.name:POST /v1/todos/` | Find specific endpoint calls |
| `level:error` | Find errors and exceptions |

---

## OpenTelemetry Compatibility

Logfire uses standard OpenTelemetry protocols, meaning you can replace it with any OTEL-compatible backend:

- **Jaeger** - Open-source distributed tracing
- **Honeycomb** - Observability for distributed systems
- **Datadog** - Full-stack monitoring platform
- **Grafana Tempo** - Distributed tracing backend
- **AWS X-Ray** - AWS native tracing

To switch backends, modify `src/infrastructure/otel/logfire.py` to configure your preferred OTEL exporter instead of Logfire.

!!! info "Why Logfire by Default?"
    Logfire is included because it offers the best developer experience for Pydantic-based applications, with automatic validation error context and minimal configuration.

---

## Excluding Endpoints from Tracing

Health check endpoints are excluded by default to reduce noise:

```python title="src/infrastructure/otel/logfire.py"
logfire.instrument_django(
    excluded_urls=".*/v1/health",
    is_sql_commentor_enabled=True,
)
```

Add additional patterns using regex:

```python
excluded_urls=".*/v1/health|.*/v1/metrics|.*/readiness"
```

---

## SQL Query Commenting

The template enables SQL commentor, which adds trace context to SQL queries:

```sql
/* db_driver='psycopg', dbapi_level='2.0',
   traceparent='00-abc123-def456-01' */
SELECT * FROM todo_todo WHERE user_id = 1;
```

This allows you to correlate slow queries in your database monitoring tools with specific traces.

---

## Summary

You have learned how to:

- Configure Logfire for production observability
- Understand what gets automatically instrumented
- Protect sensitive data with scrubbing patterns
- Query and explore traces in the Logfire dashboard
- Swap Logfire for other OpenTelemetry backends

---

## Next Steps

Continue to [Step 6: Testing](06-testing.md) to write comprehensive tests for your Todo feature.

---

!!! abstract "See Also"
    - [Configure Observability](../how-to/configure-observability.md) - Detailed configuration guide
    - [Environment Variables](../reference/environment-variables.md) - Full list of configuration options
