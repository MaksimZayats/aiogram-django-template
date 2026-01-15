from http import HTTPStatus
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import HttpBearer

from infrastructure.jwt.services import JWTService


class AuthenticatedHttpRequest[UserT: AbstractBaseUser = AbstractBaseUser](HttpRequest):
    jwt_payload: dict[str, Any]
    auth: UserT
    user: UserT  # type: ignore[bad-override, assignment]


class JWTAuthFactory:
    """Factory for creating JWT auth instances with optional permission checks.

    Example:
        factory = container.resolve(JWTAuthFactory)
        basic_auth = factory()  # No permission checks
        staff_auth = factory(require_staff=True)  # Requires is_staff=True
        admin_auth = factory(require_superuser=True)  # Requires is_superuser=True
    """

    def __init__(self, jwt_service: JWTService) -> None:
        self._jwt_service = jwt_service

    def __call__(
        self,
        *,
        require_staff: bool = False,
        require_superuser: bool = False,
    ) -> JWTAuth:
        """Create a JWT auth instance.

        Args:
            require_staff: If True, require user.is_staff to be True.
            require_superuser: If True, require user.is_superuser to be True.

        Returns:
            A JWTAuth instance configured with the specified permission checks.
        """
        if require_staff or require_superuser:
            return JWTAuthWithPermissions(
                jwt_service=self._jwt_service,
                require_staff=require_staff,
                require_superuser=require_superuser,
            )
        return JWTAuth(jwt_service=self._jwt_service)


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
        request.jwt_payload = payload  # type: ignore[attr-defined, missing-attribute, unresolved-attribute]

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


class JWTAuthWithPermissions(JWTAuth):
    """JWT auth with optional is_staff/is_superuser checks."""

    def __init__(
        self,
        jwt_service: JWTService,
        *,
        require_staff: bool = False,
        require_superuser: bool = False,
    ) -> None:
        super().__init__(jwt_service)
        self._require_staff = require_staff
        self._require_superuser = require_superuser

    def authenticate(self, request: HttpRequest, token: str) -> AbstractBaseUser | None:
        user = super().authenticate(request, token)
        if user is None:
            return None

        if self._require_staff and not getattr(user, "is_staff", False):
            raise HttpError(
                status_code=HTTPStatus.FORBIDDEN,
                message="Staff access required",
            )

        if self._require_superuser and not getattr(user, "is_superuser", False):
            raise HttpError(
                status_code=HTTPStatus.FORBIDDEN,
                message="Superuser access required",
            )

        return user
