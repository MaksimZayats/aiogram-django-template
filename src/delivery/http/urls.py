from django.urls import path

from delivery.http.api import api
from delivery.http.factories import AdminSiteFactory

_admin_site_factory = AdminSiteFactory()
_admin_site = _admin_site_factory()

urlpatterns = [
    path("admin/", _admin_site.urls),
    path("api/", api.urls),
]
