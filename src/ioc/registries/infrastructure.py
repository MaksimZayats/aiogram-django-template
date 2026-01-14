from punq import Container, Scope

from infrastructure.django.auth import JWTAuth
from infrastructure.django.refresh_sessions.services import (
    RefreshSessionService,
    RefreshSessionServiceSettings,
)
from infrastructure.jwt.services import JWTService, JWTServiceSettings


def register_infrastructure(container: Container) -> None:
    _register_jwt(container)
    _register_refresh_sessions(container)
    _register_auth(container)


def _register_jwt(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(),  # type: ignore[call-arg, missing-argument]
    )

    container.register(
        JWTService,
        scope=Scope.singleton,
    )


def _register_refresh_sessions(container: Container) -> None:
    container.register(
        RefreshSessionServiceSettings,
        factory=lambda: RefreshSessionServiceSettings(),
        scope=Scope.singleton,
    )

    container.register(
        RefreshSessionService,
        scope=Scope.singleton,
    )


def _register_auth(container: Container) -> None:
    container.register(JWTAuth, scope=Scope.singleton)
