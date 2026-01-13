from aiogram import Bot, Dispatcher

from core.configs.infrastructure import configure_infrastructure
from ioc.container import get_container


def main() -> None:
    configure_infrastructure(service_name="bot")
    container = get_container()

    bot = container.resolve(Bot)
    dispatcher = container.resolve(Dispatcher)
    dispatcher.run_polling(bot)


if __name__ == "__main__":
    main()
