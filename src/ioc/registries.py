from django.contrib.auth.base_user import AbstractBaseUser
from punq import Container, Scope

from core.user.models import RefreshSession, User
from delivery.http.factories import FastAPIFactory
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class Registry:
    def register(self, container: Container) -> None:
        container.register(
            "FastAPIFactory",
            factory=lambda: container.resolve(FastAPIFactory),
            scope=Scope.singleton,
        )
        container.register(
            type[AbstractBaseUser],
            instance=User,
            scope=Scope.singleton,
        )
        container.register(
            type[BaseRefreshSession],
            instance=RefreshSession,
            scope=Scope.singleton,
        )
