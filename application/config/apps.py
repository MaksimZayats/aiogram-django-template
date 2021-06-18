from typing import Optional

from aiogram import Dispatcher
from tortoise import Tortoise

from apps import core


# Register your apps here
INSTALLED_APPS = [
    core,
]


async def register_apps(dp: Optional[Dispatcher] = None) -> None:
    """
    Establishes a connection to the database(Tortoise).\n
    Registers all installed applications.

    :param dp:
        If Dispatcher is not None — register bots modules.
    """
    from config import DatabaseConfig

    for app in INSTALLED_APPS:
        app.register(dp)

    await Tortoise.init(config=DatabaseConfig.get_tortoise_config())
