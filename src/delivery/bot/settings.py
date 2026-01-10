from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotSettings(BaseSettings):
    config = SettingsConfigDict(env_prefix="TELEGRAM_BOT_")

    token: SecretStr
