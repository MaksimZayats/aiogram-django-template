from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

from delivery.bot.handlers import router
from delivery.bot.settings import TelegramBotSettings


class BotFactory:
    def __init__(
        self,
        settings: TelegramBotSettings,
    ) -> None:
        self._settings = settings

    def __call__(self) -> Bot:
        return Bot(
            token=self._settings.token.get_secret_value(),
            default=DefaultBotProperties(
                parse_mode=self._settings.parse_mode,
            ),
        )


class DispatcherFactory:
    def __init__(
        self,
        bot: Bot,
    ) -> None:
        self._bot = bot

    def __call__(self) -> Dispatcher:
        dispatcher = Dispatcher()
        dispatcher.include_router(router)
        dispatcher.startup()(self._set_bot_commands())

        return dispatcher

    async def _set_bot_commands(self) -> None:
        await self._bot.set_my_commands(
            [
                BotCommand(command="/start", description="Re-start the bot"),
                BotCommand(command="/id", description="Get the user and chat ids"),
            ],
        )
