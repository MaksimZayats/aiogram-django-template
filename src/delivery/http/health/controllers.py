import logging
from http import HTTPStatus
from typing import Literal

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from core.health.services import HealthCheckError, HealthService
from infrastructure.delivery.controllers import Controller

logger = logging.getLogger(__name__)


class HealthCheckResponseSchema(BaseModel):
    status: Literal["ok"]


class HealthController(Controller):
    def __init__(
        self,
        health_service: HealthService,
    ) -> None:
        self._health_service = health_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/health",
            methods=["GET"],
            view_func=self.health_check,
            response=HealthCheckResponseSchema,
            auth=None,
        )

    def health_check(
        self,
        request: HttpRequest,
    ) -> HealthCheckResponseSchema:
        try:
            self._health_service.check_system_health()
        except HealthCheckError as e:
            raise HttpError(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                message="Service is unavailable",
            ) from e

        return HealthCheckResponseSchema(status="ok")
