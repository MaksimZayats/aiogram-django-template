import logging.config

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from api.configs.logging import LOGGING
from delivery.bot.configs.bot import TELEGRAM_API_TOKEN
from delivery.bot.handlers import router

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

bot = Bot(TELEGRAM_API_TOKEN, parse_mode="HTML")

dispatcher = Dispatcher()
dispatcher.include_router(router)


async def set_bot_commands() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="/start", description="Register the bot"),
            BotCommand(command="/id", description="Get the user and chat ids"),
        ],
    )


@dispatcher.startup()
async def on_startup() -> None:
    await set_bot_commands()


def run_polling() -> None:
    dispatcher.run_polling(bot)


if __name__ == "__main__":
    run_polling()
