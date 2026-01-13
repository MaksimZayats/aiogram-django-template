import os
import sys

import django
import django_stubs_ext
from dotenv import find_dotenv, load_dotenv

from infrastructure.logging.configuration import configure_logging
from infrastructure.otel.logfire import configure_logfire


def configure_infrastructure(service_name: str) -> None:
    from core.configs.core import ApplicationSettings  # noqa: PLC0415

    if "pytest" in sys.modules:
        test_env_path = find_dotenv(".env.test", raise_error_if_not_found=True)
        load_dotenv(test_env_path, override=True)

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
