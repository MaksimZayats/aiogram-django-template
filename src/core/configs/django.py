from core.configs.core import (
    ApplicationSettings,
    CacheSettings,
    DatabaseSettings,
    SecuritySettings,
    StorageSettings,
)
from delivery.http.settings import (
    AuthSettings,
    CORSSettings,
    HTTPSettings,
    NinjaSettings,
    TemplateSettings,
)
from infrastructure.django.settings.pydantic_adapter import PydanticSettingsAdapter
from infrastructure.logging.configuration import LoggingConfig

application_settings = ApplicationSettings()
security_settings = SecuritySettings()  # type: ignore[call-arg, missing-argument]
database_settings = DatabaseSettings()
storage_settings = StorageSettings()
cache_settings = CacheSettings()

logging_settings = LoggingConfig()
http_settings = HTTPSettings()
ninja_settings = NinjaSettings()
cors_settings = CORSSettings()
auth_settings = AuthSettings()
template_settings = TemplateSettings()

adapter = PydanticSettingsAdapter()
adapter.adapt(
    database_settings,
    application_settings,
    security_settings,
    storage_settings,
    cache_settings,
    logging_settings,
    http_settings,
    ninja_settings,
    cors_settings,
    template_settings,
    auth_settings,
    settings_locals=locals(),
)
