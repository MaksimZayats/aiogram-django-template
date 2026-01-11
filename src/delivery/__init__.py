# NOTE FOR AI: /delivery package has interfaces to communicate with the outside world (e.g., HTTP API, MCP, CLI, etc.)
from core import setup_environment

if __package__ is None:
    setup_environment()  # type: ignore[unreachable]
