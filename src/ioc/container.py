from punq import Container, Scope

from api.configs.settings import Settings
from api.infrastructure.django.auth import JWTAuth
from api.infrastructure.django.refresh_sessions.models import BaseRefreshSession
from api.infrastructure.django.refresh_sessions.services import (
    RefreshSessionService,
    RefreshSessionServiceSettings,
)
from api.infrastructure.jwt.service import JWTService, JWTServiceSettings
from api.user.delivery.http.controllers import UserController, UserTokenController
from api.user.models import RefreshSession


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
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
