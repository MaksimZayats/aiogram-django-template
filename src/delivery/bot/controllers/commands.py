from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from infrastructure.delivery.controllers import AsyncController


class CommandsController(AsyncController):
    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_start_command,
            Command(commands=["start"]),
        )
        registry.message.register(
            self.handle_id_command,
            Command(commands=["id"]),
        )

    async def handle_start_command(self, message: Message) -> None:
        if message.from_user is None:
            return

        await message.answer("Hello! This is a bot.")

    async def handle_id_command(self, message: Message) -> None:
        if message.from_user is None:
            return

        await message.answer(
            f"User Id: <b>{message.from_user.id}</b>\nChat Id: <b>{message.chat.id}</b>",
        )
