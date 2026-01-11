import logging
from http import HTTPStatus
from typing import Literal

from django.contrib.sessions.models import Session
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from infrastructure.delivery.controllers import Controller

logger = logging.getLogger(__name__)


class HealthCheckResponseSchema(BaseModel):
    status: Literal["ok"]


class HealthController(Controller):
    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/health",
            methods=["GET"],
            view_func=self.health_check,
            auth=None,
        )

    def health_check(
        self,
        request: HttpRequest,
    ) -> HealthCheckResponseSchema:
        try:
            Session.objects.first()
        except Exception as e:
            logger.exception("Health check failed: database is not reachable")
            raise HttpError(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                message="Service Unavailable",
            ) from e

        return HealthCheckResponseSchema(status="ok")
