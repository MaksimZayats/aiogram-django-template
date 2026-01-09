from django.contrib.admin.views.decorators import staff_member_required
from ninja import NinjaAPI

from api.user.api import router as user_router

api = NinjaAPI(docs_decorator=staff_member_required)
api.add_router(prefix="/", router=user_router)
