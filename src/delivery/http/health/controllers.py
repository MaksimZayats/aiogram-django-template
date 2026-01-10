import logging
from typing import Literal

from django.contrib.sessions.models import Session
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from infrastructure.delivery.controllers import Controller

logger = logging.getLogger(__name__)


class HealthCheckResponseSchema(BaseModel):
    status: Literal["ok", "error"]


class HealthController(Controller):
    def register_routes(self, registry: Router) -> None:
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
        except Exception:
            logger.exception("Health check failed: database is not reachable")
            return HealthCheckResponseSchema(status="error")

        return HealthCheckResponseSchema(status="ok")
