from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from infrastructure.settings.types import Environment

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class ApplicationSettings(BaseSettings):
    environment: Environment = Environment.PRODUCTION
    version: str = "0.1.0"
    time_zone: str = "UTC"


class AWSS3Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AWS_S3_")

    endpoint_url: str
    access_key_id: str
    secret_access_key: SecretStr
    protected_bucket_name: str = "protected"
    public_bucket_name: str = "public"


class RedisSettings(BaseSettings):
    redis_url: SecretStr
