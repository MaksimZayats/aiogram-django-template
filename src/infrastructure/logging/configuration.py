import logging.config
from typing import Any

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGGING_")

    level: str = "INFO"

    @computed_field()
    def settings(self) -> dict[str, Any]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "colored": {
                    "()": "colorlog.ColoredFormatter",
                    "format": "%(asctime)s %(log_color)s%(levelname)s %(name)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "colored",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["console"],
                    "level": self.level,
                    "propagate": True,
                },
                "urllib3": {
                    "level": "WARNING",
                },
                "opentelemetry.instrumentation.instrumentor": {
                    "level": "ERROR",
                },
            },
        }


def configure_logging() -> None:
    config = LoggingConfig()
    logging.config.dictConfig(config.settings)  # type: ignore[arg-type, bad-argument-type]
