from django.urls import path

from app.apps.core.web import views

# Register your urls here

urlpatterns = [path("", views.SimpleView.as_view())]

# To register this URLS
# path("core/", include("app.core.web.urls"))
