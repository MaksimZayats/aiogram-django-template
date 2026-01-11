from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from delivery.bot.handlers import router


def get_dispatcher(bot: Bot) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    dispatcher.startup()(OnStartupHandler(bot=bot))

    return dispatcher


class OnStartupHandler:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def __call__(self) -> None:
        await self._set_bot_commands()

    async def _set_bot_commands(self) -> None:
        await self._bot.set_my_commands(
            [
                BotCommand(command="/start", description="Re-start the bot"),
                BotCommand(command="/id", description="Get the user and chat ids"),
            ],
        )
