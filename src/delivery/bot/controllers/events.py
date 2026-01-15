from aiogram import Dispatcher
from aiogram.types import BotCommand

from delivery.bot.bot_factory import BotFactory
from infrastructure.delivery.controllers import AsyncController


class LifecycleEventsController(AsyncController):
    def __init__(self, bot_factory: BotFactory) -> None:
        self._bot_factory = bot_factory

    def register(self, registry: Dispatcher) -> None:
        registry.startup()(self._set_bot_commands)

    async def _set_bot_commands(self) -> None:
        bot = self._bot_factory()

        await bot.set_my_commands(
            [
                BotCommand(command="/start", description="Re-start the bot"),
                BotCommand(command="/id", description="Get the user and chat ids"),
            ],
        )
