from django.db import models


class TGUser(models.Model):
    id = models.BigIntegerField(primary_key=True, verbose_name="Telegram User ID")
    chat_id = models.BigIntegerField(verbose_name="Telegram Chat ID")
    username = models.CharField(
        max_length=64, null=True, verbose_name="Telegram Username"
    )

    objects: models.manager.BaseManager["TGUser"]

    class Meta:
        db_table = "tg_user"
