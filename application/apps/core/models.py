from orm_converter.tortoise_to_django import ConvertedModel
from tortoise import Tortoise, fields
from tortoise.models import Model


class User(Model, ConvertedModel):
    tg_id = fields.BigIntField(unique=True, description="Telegram User ID")
    chat_id = fields.BigIntField(unique=False, description="Telegram Chat ID")
    first_name = fields.CharField(max_length=64, description="Telegram Firstname")

    def __str__(self) -> str:
        return f"{self.first_name} - {self.tg_id}"

    class Meta:
        table = "user"


def register_models() -> None:
    Tortoise.init_models(
        models_paths=["apps.core.models"],
        app_label="core",
        _init_relations=False,
    )
