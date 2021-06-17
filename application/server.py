import asyncio
import os
from pathlib import Path

import uvicorn
from aiogram import Bot
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from apps.core.web.middlewares import InjectMiddleware
from config.apps import register_apps


BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.web.settings")


async def on_startup() -> None:
    load_dotenv(BASE_DIR / 'config' / '.env')
    InjectMiddleware.inject_params['bot'] = Bot(token=os.getenv('BOT_API_TOKEN'),
                                                parse_mode='HTML')

    await register_apps()


def run_server():
    app = get_asgi_application()

    loop = asyncio.get_event_loop()

    config = uvicorn.Config(app=app, loop=loop)
    server = uvicorn.Server(config=config)

    loop.create_task(on_startup())
    loop.run_until_complete(server.serve())


if __name__ == '__main__':
    run_server()
