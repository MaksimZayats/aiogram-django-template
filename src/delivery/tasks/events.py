from typing import Any

from celery.signals import beat_init, worker_init

from infrastructure.delivery.controllers import Controller


class CeleryEvents(Controller):
    def register(self, registry: None = None) -> None:  # noqa: ARG002
        worker_init.connect()(self.worker_init)
        beat_init.connect()(self.beat_init)

    def worker_init(self, *_args: Any, **_kwargs: Any) -> None:
        pass

    def beat_init(self, *_args: Any, **_kwargs: Any) -> None:
        pass
