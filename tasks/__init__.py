from __future__ import annotations

from celery.app.task import Task

Task.__class_getitem__ = classmethod(lambda cls, *_, **__: cls)  # type: ignore[attr-defined]
