#!/usr/bin/venv python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from typing import Final

_BASE_APPS_DIR: Final[str] = os.path.join("app", "apps")


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    _modify_startapp_args()

    execute_from_command_line(sys.argv)


def _modify_startapp_args() -> None:
    if "startapp" not in sys.argv:
        return

    _add_app_directory_if_not_provided()
    _add_template_if_not_provided()


def _add_template_if_not_provided() -> None:
    if "--no-template" in sys.argv:
        sys.argv.remove("--no-template")
    elif "--template" not in sys.argv:
        sys.argv.extend(("--template", os.path.join("app", "config", "__app_template__")))


def _add_app_directory_if_not_provided() -> None:
    app_name, app_directory = _get_app_parameters()
    if app_directory:
        return

    os.makedirs(os.path.join(_BASE_APPS_DIR, app_name), exist_ok=True)
    app_directory = os.path.join(_BASE_APPS_DIR, app_name)

    sys.argv.insert(sys.argv.index(app_name) + 1, app_directory)


def _get_app_parameters() -> tuple[str, str]:
    """
    Returns a tuple of (app_name, app_directory) from the command line arguments.
    """
    app_name = ""
    app_directory = ""

    startapp_index = sys.argv.index("startapp")
    for index in range(startapp_index + 1, len(sys.argv)):
        if sys.argv[index - 1].startswith("-") or sys.argv[index].startswith("-"):
            continue

        if not app_name:
            app_name = sys.argv[index]
        elif not app_directory:
            app_directory = sys.argv[index]
        else:
            raise ValueError("Too many positional arguments for startapp command.")

    return app_name, app_directory


if __name__ == "__main__":
    main()
