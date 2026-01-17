import logging
from dataclasses import dataclass
from typing import Protocol

import logfire
from logfire import ScrubbingOptions
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from infrastructure.settings.types import Environment

logger = logging.getLogger(__name__)


class ApplicationSettingsProtocol(Protocol):
    version: str
    environment: Environment


class LogfireSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGFIRE_")

    enabled: bool = False
    token: SecretStr | None = None

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.token is not None


@dataclass
class LogfireConfigurator:
    _application_settings: ApplicationSettingsProtocol
    _logfire_settings: LogfireSettings

    def configure(
        self,
        service_name: str,
    ) -> None:
        if not self._logfire_settings.is_enabled:
            logger.debug("Logfire is disabled; skipping configuration")
            return

        logfire.configure(
            service_name=service_name,
            service_version=self._application_settings.version,
            environment=self._application_settings.environment,
            token=self._logfire_settings.token.get_secret_value(),  # type: ignore[union-attr, possibly-missing-attribute]
            scrubbing=ScrubbingOptions(
                extra_patterns=[
                    "access_token",
                    "refresh_token",
                ],
            ),
        )

        logger.info("Logfire has been configured for service: %s", service_name)
        logfire.info("Logfire has been configured for service")
