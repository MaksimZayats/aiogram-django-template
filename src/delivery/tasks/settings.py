from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.configs.core import RedisSettings


class CelerySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CELERY_")

    redis_settings: RedisSettings = Field(default_factory=RedisSettings)  # type: ignore[arg-type]
