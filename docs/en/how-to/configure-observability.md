# Configure Observability

This guide covers setting up observability with Logfire or alternative OpenTelemetry backends.

## Logfire (Default)

### Enable Logfire

Set environment variables:

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=your_write_token_here
```

### Get a Logfire Token

1. Go to [https://logfire.pydantic.dev/](https://logfire.pydantic.dev/)
2. Create an account
3. Create a new project
4. Navigate to Project Settings → Write Tokens
5. Generate a new write token

### What's Auto-Instrumented

Once enabled, Logfire automatically instruments:

| Component | Traces |
|-----------|--------|
| Django | Requests, middleware, views |
| Celery | Task execution, retries, failures |
| PostgreSQL | Queries with trace context |
| Redis | Cache operations |
| HTTP clients | requests, httpx, aiohttp |
| Pydantic | Validation errors |

### Excluded Paths

Health check endpoints are excluded to reduce noise:

```python
# Excluded from tracing
/v1/health
```

## Alternative Backends

Since the template uses OpenTelemetry standards, you can switch to other backends.

### Jaeger

Local development with Jaeger:

```bash
# Start Jaeger
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 4317:4317 \
  jaegertracing/all-in-one:latest

# Configure environment
LOGFIRE_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=my-app
```

Access the UI at [http://localhost:16686](http://localhost:16686).

### Honeycomb

```bash
LOGFIRE_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=your-api-key
OTEL_SERVICE_NAME=my-app
```

### Datadog

```bash
LOGFIRE_ENABLED=false
DD_AGENT_HOST=localhost
DD_TRACE_AGENT_PORT=8126
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=my-app
```

### Grafana Tempo

```bash
LOGFIRE_ENABLED=false
OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317
OTEL_SERVICE_NAME=my-app
```

## Custom Instrumentation

### Adding Spans

```python
import logfire

# Simple span
with logfire.span("process_order"):
    process_order(order)

# Span with attributes
with logfire.span("process_order", order_id=order.id, amount=order.total):
    process_order(order)

# Nested spans
with logfire.span("handle_checkout"):
    with logfire.span("validate_cart"):
        validate_cart(cart)
    with logfire.span("process_payment"):
        process_payment(payment)
    with logfire.span("send_confirmation"):
        send_confirmation(user)
```

### Structured Logging

```python
import logfire

# Structured log with attributes
logfire.info(
    "User logged in",
    user_id=user.id,
    ip_address=request.META.get("REMOTE_ADDR"),
)

# Warning with context
logfire.warning(
    "Rate limit approaching",
    user_id=user.id,
    current_requests=current,
    limit=max_requests,
)

# Error with exception
try:
    process_data(data)
except ValueError as e:
    logfire.error(
        "Data processing failed",
        error=str(e),
        data_id=data.id,
    )
```

### Recording Exceptions

```python
import logfire

try:
    risky_operation()
except Exception as e:
    logfire.exception("Operation failed")
    raise
```

## Scrubbing Sensitive Data

### Default Scrubbing

Logfire automatically scrubs common sensitive patterns:

- `password`
- `secret`
- `token`
- `api_key`
- `authorization`
- `cookie`

### Custom Scrubbing

The template adds additional patterns:

```python
# Custom patterns scrubbed
- access_token
- refresh_token
```

### Adding More Patterns

To add custom scrubbing patterns, configure Logfire:

```python
import logfire

logfire.configure(
    scrubbing=logfire.ScrubbingOptions(
        extra_patterns=[
            "credit_card",
            "social_security",
            "bank_account",
        ],
    ),
)
```

## SQL Query Comments

PostgreSQL queries include trace context:

```sql
/* traceparent=00-abc123-def456-01 */
SELECT * FROM core_user WHERE id = 1;
```

This allows correlating slow queries with specific requests in your observability dashboard.

## Trace Propagation

### HTTP Requests

Traces automatically propagate through HTTP requests:

```python
import httpx

# Trace context is automatically added to headers
response = httpx.get("https://api.example.com/data")
```

### Celery Tasks

Traces propagate from HTTP requests to background tasks:

```python
# HTTP handler
def create_order(request, body):
    # This span is the parent
    order = self._order_service.create_order(...)

    # Task inherits trace context
    tasks.send_order_confirmation.delay(order.id)
```

## Environment-Specific Configuration

### Development

```bash
LOGFIRE_ENABLED=false  # Disable in development
# Or use local Jaeger
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Staging

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=staging_token
LOGFIRE_PROJECT=my-app-staging
```

### Production

```bash
LOGFIRE_ENABLED=true
LOGFIRE_TOKEN=production_token
LOGFIRE_PROJECT=my-app-production
```

## Best Practices

### 1. Use Structured Data

```python
# ✅ GOOD - Structured, queryable
logfire.info("Order created", order_id=123, total=99.99, items=5)

# ❌ BAD - String interpolation
logfire.info(f"Order 123 created with total $99.99 and 5 items")
```

### 2. Add Context to Errors

```python
# ✅ GOOD - Context for debugging
try:
    process_order(order)
except PaymentError as e:
    logfire.error(
        "Payment failed",
        order_id=order.id,
        payment_method=order.payment_method,
        error_code=e.code,
    )

# ❌ BAD - No context
logfire.error("Payment failed")
```

### 3. Use Appropriate Log Levels

| Level | Use Case |
|-------|----------|
| `debug` | Detailed debugging info |
| `info` | Normal operations |
| `warning` | Unusual but handled situations |
| `error` | Errors that need attention |
| `exception` | Errors with stack trace |

### 4. Span Names Should Be Constants

```python
# ✅ GOOD - Constant name, dynamic attributes
with logfire.span("process_order", order_id=order.id):
    ...

# ❌ BAD - Dynamic name makes grouping impossible
with logfire.span(f"process_order_{order.id}"):
    ...
```

## Troubleshooting

### No Traces Appearing

1. Check `LOGFIRE_ENABLED=true`
2. Verify `LOGFIRE_TOKEN` is correct
3. Ensure network can reach Logfire API

### Missing Database Queries

Ensure Django database backend supports tracing:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # ...
    }
}
```

### High Cardinality Warnings

Avoid dynamic span names or attributes with unbounded values:

```python
# ❌ BAD - Unbounded cardinality
logfire.info("Request", path=request.path)  # Could be infinite paths

# ✅ GOOD - Bounded cardinality
logfire.info("Request", endpoint=endpoint_name)  # Known set of endpoints
```

## Related

- [Tutorial: Observability](../tutorial/05-observability.md) - Getting started
- [Pydantic Settings](../concepts/pydantic-settings.md) - Configuration
