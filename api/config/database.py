from __future__ import annotations

import logging
from os import getenv

import dj_database_url

logger = logging.getLogger(__name__)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

_default_db_url = "sqlite:///db.sqlite3"
DB_URL = getenv("DATABASE_URL", default=_default_db_url)

if _default_db_url == DB_URL:
    logger.warning("Using default database url: '%s'", DB_URL)

CONN_MAX_AGE = int(getenv("CONN_MAX_AGE", default="600"))
DATABASES = {
    "default": dj_database_url.parse(DB_URL, conn_max_age=CONN_MAX_AGE),
}
