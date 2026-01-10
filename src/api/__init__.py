import os
from functools import cache

import django
import django_stubs_ext
from dotenv import load_dotenv

from api.configs.logging import setup_logging


@cache
def setup_environment() -> None:
    load_dotenv()
    setup_logging()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.configs.settings")

    django_stubs_ext.monkeypatch()
    django.setup()


setup_environment()
