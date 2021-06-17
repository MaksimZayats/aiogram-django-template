import asyncio
import os
from pathlib import Path

from aiogram import Bot
from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from apps.core.web.middlewares import InjectMiddleware
from config.apps import register_apps


if __name__ == '__main__':
    print('To run server use `uvicorn`\n'
          'Example: uvicorn server:app')
    exit(0)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.web.settings")
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / 'config' / '.env')

app = get_asgi_application()

InjectMiddleware.inject_params['bot'] = Bot(token=os.getenv('BOT_API_TOKEN'))

loop = asyncio.get_running_loop()
loop.create_task(register_apps())
