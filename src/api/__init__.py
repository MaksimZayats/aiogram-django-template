import os

import django

__version__ = "0.0.0"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "api.config.settings")
django.setup()
