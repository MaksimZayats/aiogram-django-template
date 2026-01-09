import os

import django
import django_stubs_ext
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.configs.settings")
django_stubs_ext.monkeypatch()
django.setup()

__version__ = "0.0.0"
