from punq import Container, Scope

from core.configs.core import ApplicationSettings, RedisSettings
from core.user.models import RefreshSession
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


def register_core(container: Container) -> None:
    _register_settings(container)
    _register_models(container)


def _register_settings(container: Container) -> None:
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )

    container.register(
        RedisSettings,
        factory=lambda: RedisSettings(),  # type: ignore[call-arg, missing-argument]
        scope=Scope.singleton,
    )


def _register_models(container: Container) -> None:
    container.register(
        type[BaseRefreshSession],
        instance=RefreshSession,
    )
