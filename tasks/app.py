from __future__ import annotations

from celery import Celery

from api.config import celery as config

app = Celery("main")
app.config_from_object(config)
app.autodiscover_tasks()
