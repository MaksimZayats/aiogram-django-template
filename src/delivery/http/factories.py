
from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI, Router

from core.configs.core import ApplicationSettings
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from infrastructure.settings.types import Environment


class NinjaAPIFactory:
    def __init__(
        self,
        settings: ApplicationSettings,
        health_controller: HealthController,
        user_token_controller: UserTokenController,
        user_controller: UserController,
    ) -> None:
        self._settings = settings
        self._health_controller = health_controller
        self._user_token_controller = user_token_controller
        self._user_controller = user_controller

    def __call__(
        self,
        urls_namespace: str | None = None,
    ) -> NinjaAPI:
        if self._settings.environment == Environment.PRODUCTION:
            docs_decorator = staff_member_required
        else:
            docs_decorator = None

        ninja_api = NinjaAPI(
            urls_namespace=urls_namespace,
            docs_decorator=docs_decorator,
        )

        health_router = Router(tags=["health"])
        ninja_api.add_router("/", health_router)
        self._health_controller.register(registry=health_router)

        user_router = Router(tags=["user"])
        ninja_api.add_router("/", user_router)
        self._user_controller.register(registry=user_router)
        self._user_token_controller.register(registry=user_router)

        return ninja_api
