#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import logging
import sys

from django.core.management import execute_from_command_line

from api import setup_environment

logger = logging.getLogger(__name__)


def main() -> None:
    setup_environment()
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
