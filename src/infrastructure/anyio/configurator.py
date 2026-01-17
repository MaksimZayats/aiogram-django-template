import logging

import anyio
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

class AnyIOSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANYIO_")

    thread_limiter_tokens: int = 40


class AnyIOConfigurator:
    def __init__(self, settings: AnyIOSettings) -> None:
        self._settings = settings

    def configure(self) -> None:
        limiter = anyio.to_thread.current_default_thread_limiter()
        limiter.total_tokens = self._settings.thread_limiter_tokens

        logger.info(
            "Configured AnyIO with thread_limiter_tokens=%d",
            self._settings.thread_limiter_tokens,
        )
