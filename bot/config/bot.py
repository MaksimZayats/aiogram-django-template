from __future__ import annotations

import logging
import sys
from enum import Enum
from os import getenv

logger = logging.getLogger(__name__)


class RunningMode(str, Enum):
    LONG_POLLING = "LONG_POLLING"
    WEBHOOK = "WEBHOOK"


TELEGRAM_API_TOKEN = getenv("TELEGRAM_API_TOKEN", default="")
if not TELEGRAM_API_TOKEN:
    logger.error("`TELEGRAM_API_TOKEN` is not set")
    sys.exit(1)

RUNNING_MODE = RunningMode(getenv("RUNNING_MODE", default="LONG_POLLING"))
WEBHOOK_URL = getenv("WEBHOOK_URL", default="")
