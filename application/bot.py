import logging
from os import getenv
from pathlib import Path

from aiogram import Bot, Dispatcher, executor
from dotenv import load_dotenv

from config.apps import register_apps


BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(level=logging.INFO)


async def on_startup(dp: Dispatcher):
    await register_apps(dp)


async def on_shutdown(dp: Dispatcher):
    pass


def run_bot():
    load_dotenv(BASE_DIR / 'config' / '.env')

    bot = Bot(token=getenv('BOT_API_TOKEN'), parse_mode='HTML')
    dp = Dispatcher(bot=bot)

    executor.start_polling(
        dp, on_startup=on_startup, on_shutdown=on_shutdown)


if __name__ == '__main__':
    run_bot()
