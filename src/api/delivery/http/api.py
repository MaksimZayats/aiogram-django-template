
from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI, Router

from api.user.delivery.http.controllers import UserController, UserTokenController
from ioc.container import get_container


def get_ninja_api() -> NinjaAPI:
    container = get_container()

    api = NinjaAPI(docs_decorator=staff_member_required)

    user_router = Router(tags=["user"])
    api.add_router("/", user_router)

    for controller_class in (UserTokenController, UserController):
        controller = container.resolve(controller_class)
        controller.register_routes(router=user_router)

    return api


api = get_ninja_api()
