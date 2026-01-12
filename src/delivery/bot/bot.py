from aiogram import Bot
from aiogram.client.default import DefaultBotProperties

from delivery.bot.settings import TelegramBotSettings


def get_bot() -> Bot:
    settings = TelegramBotSettings()  # type: ignore[call-arg, missing-argument]
    return Bot(
        token=settings.token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=settings.parse_mode,
        ),
    )
