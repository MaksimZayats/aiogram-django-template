import logging.config
import os

import django
import django_stubs_ext
from dotenv import load_dotenv

from infrastructure.logging.configuration import LoggingSettings


class InfrastructureConfigurator:
    def __init__(
        self,
        logging_settings: LoggingSettings,
    ) -> None:
        self._logging_settings = logging_settings

    def configure(self) -> None:
        self._load_dotenv()
        self._configure_logging()
        self._setup_django()

    def _load_dotenv(self) -> None:
        load_dotenv(override=False)

    def _configure_logging(self) -> None:
        logging.config.dictConfig(self._logging_settings.settings)  # type: ignore[arg-type, bad-argument-type]

    def _setup_django(self) -> None:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configs.django")
        django_stubs_ext.monkeypatch()
        django.setup()
