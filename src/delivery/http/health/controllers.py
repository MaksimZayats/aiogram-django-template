from typing import Literal

from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from infrastructure.django.controller import Controller


class HealthCheckResponseSchema(BaseModel):
    status: Literal["ok"]


class HealthController(Controller):
    def register_routes(self, router: Router) -> None:
        router.add_api_operation(
            path="v1/health",
            methods=["GET"],
            view_func=self.health_check,
            auth=None,
        )

    def health_check(
        self,
        request: HttpRequest,
    ) -> HealthCheckResponseSchema:
        return HealthCheckResponseSchema(status="ok")
