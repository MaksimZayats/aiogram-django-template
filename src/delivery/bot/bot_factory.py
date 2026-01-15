from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from delivery.bot.settings import TelegramBotSettings


class BotFactory:
    def __init__(
        self,
        settings: TelegramBotSettings,
    ) -> None:
        self._settings = settings
        self._bot_instance: Bot | None = None

    def __call__(self) -> Bot:
        if self._bot_instance is not None:
            return self._bot_instance

        self._bot_instance = Bot(
            token=self._settings.token.get_secret_value(),
            default=DefaultBotProperties(
                parse_mode=self._settings.parse_mode,
            ),
        )

        return self._bot_instance
