from celery import Celery

from api.configs import celery as config

app = Celery("main")
app.config_from_object(config)
app.autodiscover_tasks()
