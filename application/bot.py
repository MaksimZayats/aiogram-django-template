import logging
from os import getenv

from aiogram import Bot, Dispatcher, executor


from config.apps import register_apps


logging.basicConfig(level=logging.INFO)


async def on_startup(dp: Dispatcher):
    await register_apps(dp)


async def on_shutdown(dp: Dispatcher):
    pass


def run_bot():
    bot = Bot(token=getenv('BOT_API_TOKEN'), parse_mode='HTML')
    dp = Dispatcher(bot=bot)

    executor.start_polling(
        dp, on_startup=on_startup, on_shutdown=on_shutdown)


if __name__ == '__main__':
    from pathlib import Path
    from dotenv import load_dotenv

    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / 'config' / '.env')

    run_bot()
