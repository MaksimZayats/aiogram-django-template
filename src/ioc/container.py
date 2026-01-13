from aiogram import Bot, Dispatcher
from celery import Celery
from ninja import NinjaAPI

from delivery.bot.factories import BotFactory, DispatcherFactory
from delivery.bot.settings import TelegramBotSettings
from punq import Container, Scope

from core.configs.core import ApplicationSettings, RedisSettings
from core.user.models import RefreshSession
from delivery.http.factories import NinjaAPIFactory
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from delivery.tasks.registry import TasksRegistry
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController
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
    _register_http(container)
    _register_controllers(container)
    _register_celery(container)
    _register_bot(container)

    return container


def _register_services(container: Container) -> None:
    container.register(
        JWTServiceSettings,
        factory=lambda: JWTServiceSettings(),  # type: ignore[call-arg, missing-argument]
    )

    container.register(
        JWTService,
        scope=Scope.singleton,
    )

    container.register(
        RefreshSessionServiceSettings,
        factory=lambda: RefreshSessionServiceSettings(),
        scope=Scope.singleton,
    )

    container.register(
        type[BaseRefreshSession],
        instance=RefreshSession,
    )

    container.register(
        RefreshSessionService,
        scope=Scope.singleton,
    )

    container.register(
        RedisSettings,
        factory=lambda: RedisSettings(),  # type: ignore[call-arg, missing-argument]
        scope=Scope.singleton,
    )


def _register_http(container: Container) -> None:
    container.register(JWTAuth, scope=Scope.singleton)
    container.register(
        ApplicationSettings,
        factory=lambda: ApplicationSettings(),
        scope=Scope.singleton,
    )
    container.register(NinjaAPIFactory, scope=Scope.singleton)
    container.register(
        NinjaAPI,
        factory=lambda: container.resolve(NinjaAPIFactory)(),
        scope=Scope.singleton,
    )


def _register_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)


def _register_celery(container: Container) -> None:
    container.register(CelerySettings, factory=lambda: CelerySettings(), scope=Scope.singleton)

    container.register(CeleryAppFactory, scope=Scope.singleton)
    container.register(
        Celery,
        factory=lambda: container.resolve(CeleryAppFactory)(),
        scope=Scope.singleton,
    )

    container.register(TasksRegistryFactory, scope=Scope.singleton)
    container.register(
        TasksRegistry,
        factory=lambda: container.resolve(TasksRegistryFactory)(),
        scope=Scope.singleton,
    )

    container.register(PingTaskController, scope=Scope.singleton)


def _register_bot(container: Container) -> None:
    container.register(TelegramBotSettings, lambda: TelegramBotSettings(), scope=Scope.singleton)
    container.register(BotFactory, scope=Scope.singleton)
    container.register(
        Bot,
        factory=lambda: container.resolve(BotFactory)(),
        scope=Scope.singleton,
    )
    container.register(DispatcherFactory, scope=Scope.singleton)
    container.register(
        Dispatcher,
        factory=lambda: container.resolve(DispatcherFactory)(),
        scope=Scope.singleton,
    )
