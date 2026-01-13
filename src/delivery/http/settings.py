from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HTTPSettings(BaseSettings):
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    csrf_trusted_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])

    root_urlconf: str = "delivery.http.urls"
    wsgi_application: str = "delivery.http.app.wsgi"

    middleware: tuple[str, ...] = (
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    )


class CORSSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CORS_")

    allow_credentials: bool = True
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])


class TemplateSettings(BaseSettings):
    templates: tuple[dict[str, Any], ...] = (
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


class AuthSettings(BaseSettings):
    auth_user_model: str = "user.User"
    authentication_backends: tuple[str, ...] = ("django.contrib.auth.backends.ModelBackend",)
    password_validators: tuple[dict[str, str], ...] = (
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
