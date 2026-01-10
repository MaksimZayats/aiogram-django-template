from pathlib import Path

from configurations import Configuration
from configurations.values import (
    BooleanValue,
    DatabaseURLValue,
    IntegerValue,
    ListValue,
    SecretValue,
    Value,
)

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


class HTTPDeliverySettings:
    MIDDLEWARE = (
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    )

    ROOT_URLCONF = "api.delivery.http.urls"
    WSGI_APPLICATION = "api.delivery.http.app.wsgi"


class TemplateSettings:
    TEMPLATES = (
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    )


class AuthSettings:
    AUTH_USER_MODEL = "user.User"
    AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
    AUTH_PASSWORD_VALIDATORS = (
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    )


class SecuritySettings:
    DEBUG = BooleanValue(default=True)
    SECRET_KEY = SecretValue()

    JWT_SECRET_KEY = SecretValue(environ_prefix=None)
    REFRESH_TOKEN_LIFETIME_MINUTES = IntegerValue(default=60 * 24 * 7)  # 7 days
    ACCESS_TOKEN_LIFETIME_MINUTES = IntegerValue(default=15)

    ALLOWED_HOSTS = ListValue(default=["127.0.0.1", "localhost"])
    CSRF_TRUSTED_ORIGINS = ListValue(default=["http://localhost"])


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


class AllSettings(
    DatabaseSettings,
    ApplicationSettings,
    HTTPDeliverySettings,
    TemplateSettings,
    AuthSettings,
    SecuritySettings,
    StorageSettings,
):
    pass


class Settings(
    AllSettings,
    Configuration,
):
    pass
