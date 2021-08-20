from django.contrib import admin

from .. import models

# Register your models here.
# To get django model: models.<ModelName>.DjangoModel


@admin.register(models.User.DjangoModel)
class UserAdmin(admin.ModelAdmin):
    pass
