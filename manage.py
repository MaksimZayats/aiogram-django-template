"""Django's command-line utility for administrative tasks."""

import sys

from django.core.management import execute_from_command_line

from core.configs.infrastructure import configure_infrastructure


def main() -> None:
    configure_infrastructure(service_name="http")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
