from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2wsgi import WSGIMiddleware
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from configs.core import ApplicationSettings
from delivery.http.django.factories import DjangoWSGIFactory
from delivery.http.health.controllers import HealthController
from delivery.http.settings import HTTPSettings
from delivery.http.user.controllers import UserController, UserTokenController
from infrastructure.anyio.configurator import AnyIOConfigurator
from infrastructure.settings.types import Environment
from infrastructure.telemetry.configurator import LogfireConfigurator
from infrastructure.telemetry.instrumentor import OpenTelemetryInstrumentor


class Lifespan:
    def __init__(
        self,
        anyio_configurator: AnyIOConfigurator,
        logfire_configurator: LogfireConfigurator,
    ) -> None:
        self._anyio_configurator = anyio_configurator
        self._logfire_configurator = logfire_configurator

    @asynccontextmanager
    async def __call__(self, _app: FastAPI) -> AsyncIterator[None]:
        self._anyio_configurator.configure()
        self._logfire_configurator.configure(service_name="fastapi")

        yield


class FastAPIFactory:
    def __init__(
        self,
        application_settings: ApplicationSettings,
        http_settings: HTTPSettings,
        telemetry_instrumentor: OpenTelemetryInstrumentor,
        lifespan: Lifespan,
        django_wsgi_factory: DjangoWSGIFactory,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
    ) -> None:
        self._application_settings = application_settings
        self._http_settings = http_settings
        self._telemetry_instrumentor = telemetry_instrumentor
        self._django_wsgi_factory = django_wsgi_factory
        self._lifespan = lifespan

        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller

    def __call__(
        self,
        *,
        include_django: bool = True,
        add_trusted_hosts_middleware: bool = True,
        add_cors_middleware: bool = True,
    ) -> FastAPI:
        docs_url = (
            "/api/docs"
            if self._application_settings.environment != Environment.PRODUCTION
            else None
        )

        app = FastAPI(
            title="API",
            lifespan=self._lifespan,
            docs_url=docs_url,
            redoc_url=None,
        )

        self._telemetry_instrumentor.instrument_fastapi(app=app)

        if add_trusted_hosts_middleware:
            app.add_middleware(
                TrustedHostMiddleware,  # type: ignore[invalid-argument-type]
                allowed_hosts=self._http_settings.allowed_hosts,
            )

        if add_cors_middleware:
            app.add_middleware(
                CORSMiddleware,  # type: ignore[invalid-argument-type]
                allow_origins=self._http_settings.cors_allow_origins,
                allow_credentials=self._http_settings.cors_allow_credentials,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        api_router = APIRouter(prefix="/api")
        self._health_controller.register(api_router)
        self._user_controller.register(api_router)
        self._user_token_controller.register(api_router)
        app.include_router(api_router)

        if include_django:
            django_wsgi = self._django_wsgi_factory()
            app.mount("/django", WSGIMiddleware(django_wsgi))  # type: ignore[arg-type, invalid-argument-type]

        return app
