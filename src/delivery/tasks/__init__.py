from celery.app.task import Task

from core.configs.infrastructure import configure_infrastructure as _configure_infrastructure

Task.__class_getitem__ = classmethod(lambda cls, *_, **__: cls)  # type: ignore[attr-defined]

_configure_infrastructure(service_name="celery")
