from __future__ import annotations

from os import getenv

USE_SILK = getenv("USE_SILK", default="false").lower() == "true"
SILKY_MIDDLEWARE_CLASS = "silk.middleware.SilkyMiddleware"

SILKY_AUTHENTICATION = True  # User must login
SILKY_AUTHORISATION = True  # User must have permissions
