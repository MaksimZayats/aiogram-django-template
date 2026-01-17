from punq import Container, Scope

from configs.core import ApplicationSettings
from delivery.http.factories import FastAPIFactory
from infrastructure.telemetry.configurator import ApplicationSettingsProtocol


class Registry:
    def register(self, container: Container) -> None:
        container.register(
            "FastAPIFactory",
            factory=lambda: container.resolve(FastAPIFactory),
            scope=Scope.singleton,
        )
        container.register(
            ApplicationSettingsProtocol,
            factory=lambda: container.resolve(ApplicationSettings),
            scope=Scope.singleton,
        )
