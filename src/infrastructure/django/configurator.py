import logging.config
import os

import django
import django_stubs_ext
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class DjangoConfigurator:
    def configure(self) -> None:
        self._load_dotenv()
        self._setup()

        logger.info("Django has been configured successfully.")

    def _load_dotenv(self) -> None:
        load_dotenv(override=False)

    def _setup(self) -> None:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configs.django")
        django_stubs_ext.monkeypatch()
        django.setup()
