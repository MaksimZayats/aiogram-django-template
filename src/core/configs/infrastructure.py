import os

import django
import django_stubs_ext
from dotenv import load_dotenv

from infrastructure.logging.configuration import configure_logging
from infrastructure.otel.logfire import configure_logfire


def configure_infrastructure(service_name: str) -> None:
    from core.configs.core import ApplicationSettings  # noqa: PLC0415

    load_dotenv(override=False)
    configure_logging()
    application_settings = ApplicationSettings()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.configs.django")

    django_stubs_ext.monkeypatch()
    django.setup()

    configure_logfire(
        service_name=service_name,
        environment=application_settings.environment,
        version=application_settings.version,
    )
