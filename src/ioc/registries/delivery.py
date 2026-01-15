from punq import Container, Scope

from delivery.bot.bot_factory import BotFactory
from delivery.bot.controllers.commands import CommandsController
from delivery.bot.controllers.events import LifecycleEventsController
from delivery.bot.dispatcher_factory import DispatcherFactory
from delivery.bot.settings import TelegramBotSettings
from delivery.http.factories import AdminSiteFactory, NinjaAPIFactory, URLPatternsFactory
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController


def register_delivery(container: Container) -> None:
    _register_http(container)
    _register_http_controllers(container)

    _register_celery(container)
    _register_celery_controllers(container)

    _register_bot(container)
    _register_bot_controllers(container)


def _register_http(container: Container) -> None:
    container.register(NinjaAPIFactory, scope=Scope.singleton)
    container.register(AdminSiteFactory, scope=Scope.singleton)
    container.register(URLPatternsFactory, scope=Scope.singleton)


def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)


def _register_celery(container: Container) -> None:
    container.register(CelerySettings, factory=lambda: CelerySettings(), scope=Scope.singleton)
    container.register(CeleryAppFactory, scope=Scope.singleton)
    container.register(TasksRegistryFactory, scope=Scope.singleton)


def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)


def _register_bot(container: Container) -> None:
    container.register(
        TelegramBotSettings,
        lambda: TelegramBotSettings(),  # type: ignore[call-arg, missing-argument]
        scope=Scope.singleton,
    )

    container.register(BotFactory, scope=Scope.singleton)
    container.register(DispatcherFactory, scope=Scope.singleton)


def _register_bot_controllers(container: Container) -> None:
    container.register(LifecycleEventsController, scope=Scope.singleton)
    container.register(CommandsController, scope=Scope.singleton)
