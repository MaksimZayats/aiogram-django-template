from pathlib import Path
from typing import Any

import dj_database_url
from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from delivery.http.settings import AuthSettings, HTTPSettings, TemplateSettings
from infrastructure.django.pydantic_settings.adapter import PydanticSettingsAdapter

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
    environment: str = "local"
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

    debug: bool = True
    secret_key: SecretStr


class StorageSettings(BaseSettings):
    static_root: Path = BASE_DIR / "static"
    static_url: str = "static/"

    media_root: Path = BASE_DIR / "media"
    media_url: str = "media/"

    @computed_field()
    def storages(self) -> dict[str, Any]:
        return {
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
                "LOCATION": self.media_root.as_posix(),
                "BASE_URL": self.media_url,
            },
        }


application_settings = ApplicationSettings()
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
