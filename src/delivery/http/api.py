from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI, Router
from punq import Container

from core.configs.settings import application_settings
from delivery.http.health.controllers import HealthController
from delivery.http.user.controllers import UserController, UserTokenController
from infrastructure.settings.types import Environment
from ioc.container import get_container


def get_ninja_api(
    container: Container | None = None,
    urls_namespace: str | None = None,
    # NOTE FOR AI: we are having both options to customize api creation for tests
) -> NinjaAPI:
    container = container or get_container()

    if application_settings.environment == Environment.PRODUCTION:
        docs_decorator = staff_member_required
    else:
        docs_decorator = None

    ninja_api = NinjaAPI(
        urls_namespace=urls_namespace,
        docs_decorator=docs_decorator,
    )

    health_router = Router(tags=["health"])
    ninja_api.add_router("/", health_router)

    health_controller = container.resolve(HealthController)
    health_controller.register(registry=health_router)

    user_router = Router(tags=["user"])
    ninja_api.add_router("/", user_router)

    for controller_class in (
        UserTokenController,
        UserController,
    ):
        controller = container.resolve(controller_class)  # type: ignore[bad-argument-type]
        controller.register(registry=user_router)

    return ninja_api


api = get_ninja_api()
