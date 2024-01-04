from __future__ import annotations

from api.user.views import router

urlpatterns = [
    *router.urls,
]
