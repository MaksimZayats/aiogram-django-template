from pathlib import Path

from configurations import Configuration
from configurations.values import (
    BooleanValue,
    DatabaseURLValue,
    IntegerValue,
    SecretValue,
    Value,
)

from delivery.http.settings import AuthSettings, HTTPSettings, TemplateSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class DatabaseSettings:
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
    DATABASES = DatabaseURLValue(default="sqlite:///db.sqlite3", alias="default")
    CONN_MAX_AGE = IntegerValue(default=600)


class ApplicationSettings:
    ENVIRONMENT = Value(default="local")
    LANGUAGE_CODE = "en-us"
    USE_TZ = True
    TIME_ZONE = "UTC"
    INSTALLED_APPS = (
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "api.user.apps.UserConfig",
    )


class SecuritySettings:
    DEBUG = BooleanValue(default=True)
    SECRET_KEY = SecretValue()
    JWT_SECRET_KEY = SecretValue(environ_prefix=None)


class StorageSettings:
    STATIC_ROOT = BASE_DIR / "staticfiles"
    STATIC_URL = "static/"

    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "media/"

    STORAGES = {
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "LOCATION": MEDIA_ROOT.as_posix(),
            "BASE_URL": MEDIA_URL,
        },
    }


class Settings(
    DatabaseSettings,
    ApplicationSettings,
    SecuritySettings,
    StorageSettings,
    HTTPSettings,
    TemplateSettings,
    AuthSettings,
    Configuration,
):
    pass
