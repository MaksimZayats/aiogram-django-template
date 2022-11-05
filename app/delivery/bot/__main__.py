import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from app.apps.core.bot.handlers import router as core_router
from app.config.bot import RUNNING_MODE, TG_TOKEN, RunningMode

bot = Bot(TG_TOKEN, parse_mode="HTML")

dispatcher = Dispatcher()
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def _register_routers() -> None:
    dispatcher.include_router(core_router)


async def _set_bot_commands() -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="/start", description="Start bot"),
            BotCommand(command="/apps", description="Show installed apps"),
        ]
    )


@dispatcher.startup()
async def on_startup() -> None:
    # Register all routers
    _register_routers()

    # Set default commands
    await _set_bot_commands()


def run_polling() -> None:
    dispatcher.run_polling(bot)


def run_webhook() -> None:
    raise NotImplementedError("Webhook mode is not implemented yet")


if __name__ == "__main__":
    if RUNNING_MODE == RunningMode.LONG_POLLING:
        run_polling()
    elif RUNNING_MODE == RunningMode.WEBHOOK:
        run_webhook()
    else:
        raise RuntimeError(f"Unknown running mode: {RUNNING_MODE}")
