import asyncio
import logging
import os
from multiprocessing import Process
from os import getenv
from pathlib import Path

import uvicorn
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from apps.core.web.middlewares import InjectMiddleware
from config.apps import register_apps

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.web.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

load_dotenv(BASE_DIR / "config" / ".env")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class MyBot:
    storage = MemoryStorage()

    bot = Bot(token=getenv("BOT_API_TOKEN"), parse_mode="HTML")
    dp = Dispatcher(bot=bot, storage=storage)

    Bot.set_current(bot)
    Dispatcher.set_current(dp)

    @classmethod
    def run(cls):
        executor.start_polling(
            cls.dp, on_startup=cls.on_startup, on_shutdown=cls.on_shutdown
        )

    @staticmethod
    async def on_startup(dp: Dispatcher):
        await register_apps(dp)

    @staticmethod
    async def on_shutdown(dp: Dispatcher):
        pass


class MyServer:
    app = get_asgi_application()

    config = uvicorn.Config(app=app, loop=loop, port=8001)
    server = uvicorn.Server(config=config)

    @classmethod
    def run(cls):
        asyncio.run(cls.on_startup())
        asyncio.run(cls.server.serve())
        asyncio.run(cls.on_shutdown())

    @staticmethod
    async def on_startup() -> None:
        InjectMiddleware.inject_params = dict(bot=MyBot.bot)

        await register_apps()

    @staticmethod
    async def on_shutdown() -> None:
        pass


def run_app():
    bot = Process(target=MyBot.run)
    server = Process(target=MyServer.run)

    bot.start()
    server.start()


if __name__ == "__main__":
    run_app()
