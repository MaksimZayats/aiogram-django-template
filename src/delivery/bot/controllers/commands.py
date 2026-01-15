from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from asgiref.sync import sync_to_async

from core.health.services import HealthCheckError, HealthService
from infrastructure.delivery.controllers import AsyncController


class CommandsController(AsyncController):
    def __init__(self, health_service: HealthService) -> None:
        self._health_service = health_service

    def register(self, registry: Router) -> None:
        registry.message.register(
            self.handle_start_command,
            Command(commands=["start"]),
        )
        registry.message.register(
            self.handle_id_command,
            Command(commands=["id"]),
        )
        registry.message.register(
            self.handle_health_check_command,
            Command(commands=["health"]),
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

    async def handle_health_check_command(self, message: Message) -> None:
        if message.from_user is None:
            return

        try:
            # Run the synchronous health check in a thread to avoid blocking
            await sync_to_async(
                self._health_service.check_system_health,
                thread_sensitive=False,
            )()
            await message.answer("✅ The system is healthy.")
        except HealthCheckError as e:
            await message.answer(f"❌ Health check failed: {e}")
