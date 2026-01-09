from http import HTTPStatus
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import HttpBearer

from api.infrastructure.jwt.service import JWTService


class JWTAuth(HttpBearer):
    def __init__(
        self,
        jwt_service: JWTService,
    ) -> None:
        super().__init__()
        self._jwt_service = jwt_service
        self._user_model = get_user_model()

    def authenticate(self, request: HttpRequest, token: str) -> AbstractBaseUser | None:
        payload = self._get_token_payload(token=token)
        request.jwt_payload = payload

        user_id = payload.get("sub")
        if user_id is None:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Token payload missing 'sub' field",
            )

        try:
            user = self._user_model.objects.get(id=user_id)
        except self._user_model.DoesNotExist as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="User not found",
            ) from e

        request.user = user

        return user

    def _get_token_payload(self, token: str) -> dict[str, Any]:
        try:
            return self._jwt_service.decode_token(token=token)
        except self._jwt_service.EXPIRED_SIGNATURE_ERROR as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Token has expired",
            ) from e
        except self._jwt_service.INVALID_TOKEN_ERROR as e:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid token",
            ) from e
