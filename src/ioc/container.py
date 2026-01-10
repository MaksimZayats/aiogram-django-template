from api.configs.security import JWT_SECRET_KEY
from punq import Container, Scope

from api.infrastructure.django.auth import JWTAuth
from api.infrastructure.jwt.service import JWTService, JWTServiceSettings
from api.user.delivery.http.controllers import UserController, UserTokenController


def get_container() -> Container:
    container = Container()

    _register_services(container)
    _register_auth(container)
    _register_controllers(container)

    return container


def _register_services(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(secret_key=JWT_SECRET_KEY),
        scope=Scope.singleton,
    )

    container.register(
        JWTService,
        scope=Scope.singleton,
    )


def _register_auth(container: Container) -> None:
    container.register(JWTAuth, scope=Scope.singleton)


def _register_controllers(container: Container) -> None:
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
