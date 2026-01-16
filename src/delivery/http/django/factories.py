from django.contrib.admin import AdminSite
from django.contrib.admin.sites import site as default_site
from django.core.handlers.wsgi import WSGIHandler


class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        from delivery.http.user import admin as _user_admin  # noqa: F401, PLC0415

        return default_site


class DjangoWSGIFactory:
    def __init__(
        self,
        admin_site_factory: AdminSiteFactory,
    ) -> None:
        self._admin_site_factory = admin_site_factory

    def __call__(self) -> WSGIHandler:
        self._admin_site_factory()

        return WSGIHandler()
