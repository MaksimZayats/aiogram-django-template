# Beat Scheduler

Scheduled and periodic tasks with Celery Beat.

## Overview

Celery Beat is a scheduler that runs tasks at regular intervals:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Celery Beat │────>│    Redis    │────>│   Worker    │
│ (Scheduler) │     │  (Broker)   │     │  (Celery)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Configuration

Beat schedule is configured in `CeleryAppFactory`:

```python
# src/delivery/tasks/factories.py

class CeleryAppFactory:
    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,  # Every 60 seconds
            },
        }
```

## Schedule Types

### Fixed Interval

```python
from celery.schedules import schedule

celery_app.conf.beat_schedule = {
    "task-every-30-seconds": {
        "task": TaskName.MY_TASK,
        "schedule": 30.0,
    },
    "task-every-5-minutes": {
        "task": TaskName.ANOTHER_TASK,
        "schedule": 300.0,
    },
}
```

### Crontab

```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Every day at midnight
    "daily-cleanup": {
        "task": TaskName.CLEANUP,
        "schedule": crontab(hour=0, minute=0),
    },

    # Every Monday at 9 AM
    "weekly-report": {
        "task": TaskName.WEEKLY_REPORT,
        "schedule": crontab(hour=9, minute=0, day_of_week=1),
    },

    # Every hour at minute 30
    "hourly-sync": {
        "task": TaskName.SYNC_DATA,
        "schedule": crontab(minute=30),
    },

    # First day of every month
    "monthly-invoice": {
        "task": TaskName.GENERATE_INVOICES,
        "schedule": crontab(day_of_month=1, hour=6, minute=0),
    },
}
```

### Crontab Reference

| Field | Values | Description |
|-------|--------|-------------|
| `minute` | 0-59 | Minute of hour |
| `hour` | 0-23 | Hour of day |
| `day_of_week` | 0-6 (Mon-Sun) | Day of week |
| `day_of_month` | 1-31 | Day of month |
| `month_of_year` | 1-12 | Month |

Special values:

- `*` — Every (default)
- `*/5` — Every 5th (e.g., `minute="*/5"` = every 5 minutes)
- `1,15` — Specific values (e.g., `day_of_month="1,15"` = 1st and 15th)

### Solar Schedule

```python
from celery.schedules import solar

celery_app.conf.beat_schedule = {
    "lights-on-at-sunset": {
        "task": TaskName.TURN_ON_LIGHTS,
        "schedule": solar("sunset", -37.8136, 144.9631),  # Melbourne
    },
}
```

## Task Arguments

Pass arguments to scheduled tasks:

```python
celery_app.conf.beat_schedule = {
    "cleanup-30-days": {
        "task": TaskName.CLEANUP_SESSIONS,
        "schedule": crontab(hour=2, minute=0),
        "args": [30],  # Positional arguments
    },
    "cleanup-7-days": {
        "task": TaskName.CLEANUP_SESSIONS,
        "schedule": crontab(hour=3, minute=0),
        "kwargs": {"days_old": 7},  # Keyword arguments
    },
}
```

## Task Options

```python
celery_app.conf.beat_schedule = {
    "important-task": {
        "task": TaskName.IMPORTANT_TASK,
        "schedule": 60.0,
        "options": {
            "queue": "high_priority",
            "expires": 30,  # Expire if not run within 30 seconds
        },
    },
}
```

## Running Beat

### Development

```bash
make celery-beat-dev
```

### Production (Docker Compose)

```yaml
celery-beat:
  command:
    - celery
    - --app=delivery.tasks.app
    - beat
    - --loglevel=${LOGGING_LEVEL:-INFO}
```

!!! warning "Single Instance"
    Only run one Beat instance. Multiple instances will duplicate scheduled tasks.

## Complete Example

```python
# src/delivery/tasks/factories.py

from celery.schedules import crontab

from delivery.tasks.registry import TaskName


class CeleryAppFactory:
    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            # Health check every minute
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },

            # Clean up old sessions daily at 2 AM
            "cleanup-sessions-daily": {
                "task": TaskName.CLEANUP_SESSIONS,
                "schedule": crontab(hour=2, minute=0),
                "args": [30],
            },

            # Send daily digest at 8 AM
            "daily-digest": {
                "task": TaskName.SEND_DAILY_DIGEST,
                "schedule": crontab(hour=8, minute=0),
            },

            # Sync external data every 15 minutes
            "sync-data": {
                "task": TaskName.SYNC_EXTERNAL_DATA,
                "schedule": crontab(minute="*/15"),
            },

            # Generate weekly report on Monday at 9 AM
            "weekly-report": {
                "task": TaskName.GENERATE_WEEKLY_REPORT,
                "schedule": crontab(hour=9, minute=0, day_of_week=1),
            },
        }
```

## Timezone

Set timezone for schedule calculations:

```python
# In CeleryAppFactory._configure_app()
celery_app.conf.update(timezone="UTC")
```

Or use your application timezone:

```python
from core.configs.django import application_settings

celery_app.conf.update(timezone=application_settings.time_zone)
```

## Monitoring

### Check Schedule

```bash
celery -A delivery.tasks.app inspect scheduled
```

### View Active Tasks

```bash
celery -A delivery.tasks.app inspect active
```

### Reserved Tasks

```bash
celery -A delivery.tasks.app inspect reserved
```

## Troubleshooting

### Tasks Not Running

1. Ensure Beat is running: `docker compose ps celery-beat`
2. Check Beat logs: `docker compose logs celery-beat`
3. Verify worker is running: `docker compose ps celery-worker`
4. Check Redis connection: `docker compose logs redis`

### Duplicate Tasks

- Only run one Beat instance
- Check for multiple Beat containers

### Tasks Running Late

- Check worker concurrency
- Look for long-running tasks blocking the queue
- Consider using separate queues for scheduled tasks

## Related Topics

- [Task Controllers](task-controllers.md) — Creating tasks
- [Task Registry](task-registry.md) — Task access
- [Docker Services](../reference/docker-services.md) — Container configuration
