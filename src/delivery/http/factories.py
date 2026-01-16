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
from infrastructure.settings.types import Environment


class Lifespan:
    pass


class FastAPIFactory:
    def __init__(
        self,
        application_settings: ApplicationSettings,
        http_settings: HTTPSettings,
        django_wsgi_factory: DjangoWSGIFactory,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
    ) -> None:
        self._settings = application_settings
        self._http_settings = http_settings
        self._django_wsgi_factory = django_wsgi_factory

        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller

    def __call__(
        self,
        *,
        include_admin: bool = True,
        add_trusted_hosts_middleware: bool = True,
        add_cors_middleware: bool = True,
    ) -> FastAPI:
        @asynccontextmanager
        async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
            yield

        docs_url = "/api/docs" if self._settings.environment != Environment.PRODUCTION else None

        app = FastAPI(
            title="API",
            lifespan=lifespan,
            docs_url=docs_url,
            redoc_url=None,
        )

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

        if include_admin:
            django_wsgi = self._django_wsgi_factory()
            app.mount("/admin", WSGIMiddleware(django_wsgi))  # type: ignore[arg-type, invalid-argument-type]

        return app
