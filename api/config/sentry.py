from __future__ import annotations

import logging
from os import environ, getenv

from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from api.config.application import ENVIRONMENT

logger = logging.getLogger(__name__)

USE_SENTRY = getenv("USE_SENTRY", default="false").lower() == "true"

if USE_SENTRY:
    import sentry_sdk

    DSN = environ["SENTRY_DSN"]
    TRACES_SAMPLE_RATE = float(getenv("SENTRY_TRACES_SAMPLE_RATE", default="1.0"))
    PROFILE_SAMPLE_RATE = float(
        getenv("SENTRY_PROFILE_SAMPLE_RATE", default="1.0"),
    )

    sentry_sdk.init(
        dsn=DSN,
        environment=ENVIRONMENT,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=TRACES_SAMPLE_RATE,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=PROFILE_SAMPLE_RATE,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )

    logger.info("Sentry is initialized")
else:
    logger.info("Sentry is not initialized")
