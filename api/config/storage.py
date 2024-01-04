from __future__ import annotations

import logging
from os import getenv
from typing import Any, cast

from storages.backends.s3 import S3Storage

from api.config.base import BASE_DIR

logger = logging.getLogger(__name__)

USE_S3_FOR_MEDIA = getenv("USE_S3_FOR_MEDIA", default="false").lower() == "true"
USE_S3_FOR_STATIC = getenv("USE_S3_FOR_STATIC", default="false").lower() == "true"

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "static/"

MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "media/"

AWS_STORAGE_BUCKET_NAME = getenv("AWS_STORAGE_BUCKET_NAME", "bucket")
AWS_S3_CUSTOM_DOMAIN = getenv(
    "AWS_S3_CUSTOM_DOMAIN",
    f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com",
)
AWS_S3_ENDPOINT_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}"

AWS_S3_ACCESS_KEY_ID = getenv("AWS_S3_ACCESS_KEY_ID", "access_key")
AWS_S3_SECRET_ACCESS_KEY = getenv("AWS_S3_SECRET_ACCESS_KEY", "secret_key")

AWS_S3_CONFIG = {
    "BACKEND": "api.config.storage.CustomDomainS3Storage",
    "OPTIONS": {
        "bucket_name": AWS_STORAGE_BUCKET_NAME,
        "access_key": AWS_S3_ACCESS_KEY_ID,
        "secret_key": AWS_S3_SECRET_ACCESS_KEY,
        "endpoint_url": AWS_S3_ENDPOINT_URL,
    },
}

STORAGES: dict[str, Any] = {}

if USE_S3_FOR_STATIC:
    logger.info("Serving static files from S3")
    STORAGES["staticfiles"] = AWS_S3_CONFIG
else:
    logger.info("Serving static files locally")
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    }


if USE_S3_FOR_MEDIA:
    logger.info("Serving media files from S3")
    STORAGES["default"] = AWS_S3_CONFIG
else:
    logger.info("Serving media files locally")
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "LOCATION": MEDIA_ROOT.as_posix(),
        "BASE_URL": MEDIA_URL,
    }


class CustomDomainS3Storage(S3Storage):
    """Extend S3 with signed URLs for custom domains."""

    custom_domain = False

    def url(
        self,
        name: str,
        parameters: Any = None,
        expire: Any = None,
        http_method: Any = None,
    ) -> str:
        """Replace internal domain with custom domain for signed URLs."""
        url = cast(str, super().url(name, parameters, expire, http_method))

        return url.replace(
            f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com",
            AWS_S3_ENDPOINT_URL,
        )
