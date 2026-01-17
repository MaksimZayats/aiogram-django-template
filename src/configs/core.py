from pathlib import Path

from pydantic_settings import BaseSettings

from infrastructure.settings.types import Environment

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class ApplicationSettings(BaseSettings):
    environment: Environment = Environment.PRODUCTION
    version: str = "0.1.0"
    time_zone: str = "UTC"
