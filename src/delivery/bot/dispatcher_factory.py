from aiogram import Dispatcher, Router

from delivery.bot.bot_factory import BotFactory
from delivery.bot.controllers.commands import CommandsController
from delivery.bot.controllers.events import LifecycleEventsController


class DispatcherFactory:
    def __init__(
        self,
        bot_factory: BotFactory,
        lifecycle_controller: LifecycleEventsController,
        commands_controller: CommandsController,
    ) -> None:
        self._bot_factory = bot_factory
        self._lifecycle_controller = lifecycle_controller
        self._commands_controller = commands_controller

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()
        self._lifecycle_controller.register(dispatcher)

        router = Router(name="commands")
        dispatcher.include_router(router)
        self._commands_controller.register(router)

        return dispatcher
