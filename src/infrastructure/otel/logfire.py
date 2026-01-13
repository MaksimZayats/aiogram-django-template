import logfire
from logfire import ScrubbingOptions
from logfire.integrations.psycopg import CommenterOptions
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from infrastructure.settings.types import Environment


class LogfireSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOGFIRE_")

    token: SecretStr | None = None


def configure_logfire(
    service_name: str,
    environment: Environment,
    version: str,
) -> None:
    settings = LogfireSettings()
    if settings.token is None:
        return

    logfire.configure(
        service_name=service_name,
        service_version=version,
        environment=environment,
        token=settings.token.get_secret_value(),
        scrubbing=ScrubbingOptions(
            extra_patterns=[
                "access_token",
                "refresh_token",
            ],
        ),
    )

    _instrument_libraries()


def _instrument_libraries() -> None:
    logfire.instrument_django(
        excluded_urls=".*/v1/health",
        is_sql_commentor_enabled=True,
    )
    logfire.instrument_celery(propagate_trace_context=True)
    logfire.instrument_requests()
    logfire.instrument_psycopg(
        enable_commenter=True,
        commenter_options=CommenterOptions(
            db_driver=True,
            dbapi_level=True,
        ),
    )
    logfire.instrument_httpx()
    logfire.instrument_redis()
    logfire.instrument_pydantic()
