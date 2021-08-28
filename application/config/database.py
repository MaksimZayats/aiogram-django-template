from os import getenv
from typing import Dict, Set, Type

from tortoise import Model


class DatabaseConfig:
    @staticmethod
    def get_tortoise_config():
        return {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": getenv("DB_HOST"),
                        "port": getenv("DB_PORT"),
                        "user": getenv("DB_USER"),
                        "password": getenv("DB_PASSWORD"),
                        "database": getenv("DB_NAME"),
                    },
                },
            },
            "apps": _get_inited_tortoise_apps(),
            "use_tz": False,
            "timezone": "UTC",
        }

    @staticmethod
    def get_django_config():
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": getenv("DB_HOST"),
                "PORT": getenv("DB_PORT"),
                "USER": getenv("DB_USER"),
                "PASSWORD": getenv("DB_PASSWORD"),
                "NAME": getenv("DB_NAME"),
            }
        }


def _get_inited_tortoise_apps() -> Dict[str, Dict[str, Set[str]]]:
    """
    Retrieves all registered apps for Tortoise Config

    :return: Dict of Apps for Tortoise Config
    """
    from tortoise import Tortoise

    apps: Dict[str, Dict[str, Set[str]]] = {}

    for app_name, app_models in Tortoise.apps.items():  # type: str, Dict[str, Type[Model]]
        for model_name, model_type in app_models.items():
            try:
                apps[app_name]["models"] |= {model_type.__module__}
            except KeyError:
                apps[app_name] = {"models": {model_type.__module__}}
    return apps
