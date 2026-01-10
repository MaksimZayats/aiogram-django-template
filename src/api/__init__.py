import os
from functools import cache

import django
import django_stubs_ext
from configurations import importer
from dotenv import load_dotenv


@cache
def setup_environment() -> None:
    load_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.configs.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Settings")

    importer.install()
    django_stubs_ext.monkeypatch()
    django.setup()


setup_environment()
