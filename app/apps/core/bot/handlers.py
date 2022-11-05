from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.apps.core.use_case import CORE_USE_CASE
from app.config.application import INSTALLED_APPS

router = Router()


@router.message(Command(commands=["start"]))
async def handle_start_command(message: Message) -> None:
    if message.from_user is None:
        return

    _, is_new = await CORE_USE_CASE.register_bot_user(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        username=message.from_user.username,
    )

    if is_new:
        await message.answer("You have successfully registered in the bot!")
    else:
        await message.answer("You are already registered in the bot!")


@router.message(Command(commands=["apps"]))
async def handle_apps_command(message: Message) -> None:
    apps_names = [app_name for app_name in INSTALLED_APPS if app_name.startswith("app.")]
    await message.answer("Installed apps:\n" f"{apps_names}")


@router.message(Command(commands=["id"]))
async def handle_id_command(message: Message) -> None:
    if message.from_user is None:
        return

    await message.answer(
        f"User Id: <b>{message.from_user.id}</b>\n" f"Chat Id: <b>{message.chat.id}</b>"
    )
