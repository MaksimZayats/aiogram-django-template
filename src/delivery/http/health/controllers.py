import logging
from http import HTTPStatus
from typing import Literal

from fastapi import APIRouter, HTTPException
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

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/health",
            endpoint=self.health_check,
            methods=["GET"],
        )

    def health_check(self) -> HealthCheckResponseSchema:
        try:
            self._health_service.check_system_health()
        except HealthCheckError as e:
            raise HTTPException(
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail="Service is unavailable",
            ) from e

        return HealthCheckResponseSchema(status="ok")
