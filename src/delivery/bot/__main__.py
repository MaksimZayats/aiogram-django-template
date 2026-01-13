from delivery.bot.bot import get_bot
from delivery.bot.dispatcher import get_dispatcher


def main() -> None:
    bot = get_bot()
    dispatcher = get_dispatcher(bot=bot)

    dispatcher.run_polling(bot)


if __name__ == "__main__":
    main()
