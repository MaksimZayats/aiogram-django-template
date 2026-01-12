# NOTE FOR AI: the `core` module contains the main business logic of the application
# The services are all class based with clear dependencies definitions
# All services resolved with IOC container

import os
from functools import cache

import django
import django_stubs_ext
from dotenv import load_dotenv

from core.configs.logging import setup_logging


@cache
def setup_environment() -> None:
    load_dotenv(override=False)

    setup_logging()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.configs.settings")

    django_stubs_ext.monkeypatch()
    django.setup()


setup_environment()
