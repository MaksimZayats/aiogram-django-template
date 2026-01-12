from celery.app.task import Task

from core import setup_environment

Task.__class_getitem__ = classmethod(lambda cls, *_, **__: cls)  # type: ignore[attr-defined]

setup_environment()
