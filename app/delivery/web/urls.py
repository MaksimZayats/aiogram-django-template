"""
URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, path

from app.config.application import DEBUG
from app.config.web import STATIC_ROOT, STATIC_URL

urlpatterns: list[URLResolver | URLPattern] = [
    path("admin/", admin.site.urls),
]

if DEBUG:
    # See https://docs.djangoproject.com/en/4.1/howto/static-files/#serving-files
    # https://stackoverflow.com/questions/61770551/how-to-run-django-with-uvicorn-webserver-uploaded-by-a-user-during-development
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
