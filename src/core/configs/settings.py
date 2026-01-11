from pathlib import Path
from typing import Any

import dj_database_url
from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from delivery.http.settings import AuthSettings, HTTPSettings, TemplateSettings
from infrastructure.django.settings.pydantic_adapter import PydanticSettingsAdapter
from infrastructure.settings.types import Environment

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class DatabaseSettings(BaseSettings):
    default_auto_field: str = "django.db.models.BigAutoField"
    conn_max_age: int = 600
    database_url: str = "sqlite:///db.sqlite3"

    @computed_field()
    def databases(self) -> dict[str, Any]:
        return {
            "default": dj_database_url.parse(
                self.database_url,
                conn_max_age=self.conn_max_age,
            ),
        }


class ApplicationSettings(BaseSettings):
    environment: Environment
    language_code: str = "en-us"
    use_tz: bool = True
    time_zone: str = "UTC"
    installed_apps: tuple[str, ...] = (
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "core.user.apps.UserConfig",
    )


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DJANGO_")

    debug: bool = False
    secret_key: SecretStr


class AWSS3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWS_S3_")

    endpoint_url: str
    access_key_id: str
    secret_access_key: SecretStr
    protected_bucket_name: str = "protected"
    public_bucket_name: str = "public"


class StorageSettings(BaseSettings):
    static_url: str = "static/"
    media_url: str = "media/"

    s3_settings: AWSS3Settings = Field(default_factory=AWSS3Settings)  # type: ignore[arg-type]

    @computed_field()
    def storages(self) -> dict[str, Any]:
        s3_storage_config = {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "bucket_name": self.s3_settings.protected_bucket_name,
                "access_key": self.s3_settings.access_key_id,
                "secret_key": self.s3_settings.secret_access_key.get_secret_value(),
                "endpoint_url": self.s3_settings.endpoint_url,
            },
        }

        return {
            "staticfiles": s3_storage_config,
            "default": s3_storage_config,
        }


application_settings = ApplicationSettings()  # type: ignore[call-arg, missing-argument]
security_settings = SecuritySettings()  # type: ignore[call-arg, missing-argument]
database_settings = DatabaseSettings()
storage_settings = StorageSettings()

http_settings = HTTPSettings()
auth_settings = AuthSettings()
template_settings = TemplateSettings()

adapter = PydanticSettingsAdapter()
adapter.adapt(
    database_settings,
    application_settings,
    security_settings,
    storage_settings,
    http_settings,
    template_settings,
    auth_settings,
    settings_locals=locals(),
)
