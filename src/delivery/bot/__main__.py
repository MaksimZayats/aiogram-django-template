from core.configs.infrastructure import configure_infrastructure
from delivery.bot.bot_factory import BotFactory
from delivery.bot.dispatcher_factory import DispatcherFactory
from ioc.container import get_container


def main() -> None:
    configure_infrastructure(service_name="bot")
    container = get_container()

    bot_factory = container.resolve(BotFactory)
    bot = bot_factory()

    dispatcher_factory = container.resolve(DispatcherFactory)
    dispatcher = dispatcher_factory()

    dispatcher.run_polling(bot)


if __name__ == "__main__":
    main()
