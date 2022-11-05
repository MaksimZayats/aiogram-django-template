from django.contrib import admin
from django.contrib.admin import ModelAdmin

from app.apps.core.models import TGUser


@admin.register(TGUser)
class CoreAdmin(ModelAdmin[TGUser]):
    pass
