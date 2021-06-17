from tortoise import Tortoise, fields
from tortoise.models import Model

from django.db import models as django_models


class User(Model):
    tg_id = fields.BigIntField(unique=True, description='Telegram User ID')
    chat_id = fields.BigIntField(unique=False, description='Telegram Chat ID')
    first_name = fields.CharField(max_length=64, description='Telegram Firstname')

    class DjangoModel(django_models.Model):
        __qualname__ = 'User'

        tg_id = django_models.BigIntegerField(unique=True, verbose_name='Telegram User ID')
        chat_id = django_models.BigIntegerField(unique=False, verbose_name='Telegram Chat ID')
        first_name = django_models.CharField(max_length=64, verbose_name='Telegram Firstname')

        class Meta:
            db_table = 'user'

    def __str__(self) -> str:
        return f'{self.first_name} - {self.tg_id}'

    class Meta:
        table = 'user'


def register_models() -> None:
    Tortoise.init_models(models_paths=['apps.core.models'], app_label='core')
