from __future__ import annotations

from os import getenv

AXES_ENABLED = getenv("AXES_ENABLED", default="true").lower() == "true"
AXES_FAILURE_LIMIT = int(getenv("AXES_FAILURE_LIMIT", default="5"))
