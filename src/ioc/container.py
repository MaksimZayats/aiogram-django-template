from punq import Container, Scope

from api.configs.settings import Settings
from api.user.models import RefreshSession
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from infrastructure.django.auth import JWTAuth
from infrastructure.django.refresh_sessions.models import BaseRefreshSession
from infrastructure.django.refresh_sessions.services import (
    RefreshSessionService,
    RefreshSessionServiceSettings,
)
from infrastructure.jwt.services import JWTService, JWTServiceSettings


def get_container() -> Container:
    container = Container()

    _register_services(container)
    _register_auth(container)
    _register_controllers(container)

    return container


def _register_services(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(secret_key=Settings.JWT_SECRET_KEY),  # ty: ignore[invalid-argument-type]
        scope=Scope.singleton,
    )

    container.register(
        JWTService,
        scope=Scope.singleton,
    )

    container.register(
        RefreshSessionServiceSettings,
        factory=lambda: RefreshSessionServiceSettings(),
    )

    container.register(
        type[BaseRefreshSession],
        instance=RefreshSession,
    )

    container.register(
        RefreshSessionService,
        scope=Scope.singleton,
    )


def _register_auth(container: Container) -> None:
    container.register(JWTAuth, scope=Scope.singleton)


def _register_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
