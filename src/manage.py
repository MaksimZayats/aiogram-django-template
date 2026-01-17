"""Django's command-line utility for administrative tasks."""

import sys

from django.core.management import execute_from_command_line

from ioc.container import ContainerFactory


class DjangoManager:
    def execute_from_command_line(self, argv: list[str]) -> None:
        execute_from_command_line(argv)


def main() -> None:
    container_factory = ContainerFactory()
    container = container_factory()

    manager = container.resolve(DjangoManager)
    manager.execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
