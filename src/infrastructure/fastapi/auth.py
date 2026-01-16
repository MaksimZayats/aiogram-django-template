from http import HTTPStatus
from typing import Any, Protocol, cast

from django.contrib.auth.base_user import AbstractBaseUser
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infrastructure.jwt.services import JWTService


class AuthenticatedRequestState[UserT: AbstractBaseUser = AbstractBaseUser](Protocol):
    jwt_payload: dict[str, Any]
    user: UserT


class AuthenticatedRequest[UserT: AbstractBaseUser = AbstractBaseUser](Request):
    state: AuthenticatedRequestState[UserT]  # type: ignore[bad-override, assignment]


class JWTAuthFactory:
    """Factory for creating JWT auth instances with optional permission checks.

    Example:
        factory = container.resolve(JWTAuthFactory)
        basic_auth = factory()  # No permission checks
        staff_auth = factory(require_staff=True)  # Requires is_staff=True
        admin_auth = factory(require_superuser=True)  # Requires is_superuser=True
    """

    def __init__(
        self,
        jwt_service: JWTService,
        user_model: type[AbstractBaseUser],
    ) -> None:
        self._jwt_service = jwt_service
        self._user_model = user_model

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
                user_model=self._user_model,
                require_staff=require_staff,
                require_superuser=require_superuser,
            )

        return JWTAuth(jwt_service=self._jwt_service, user_model=self._user_model)


class JWTAuth(HTTPBearer):
    def __init__(
        self,
        jwt_service: JWTService,
        user_model: type[AbstractBaseUser],
    ) -> None:
        super().__init__()
        self._jwt_service = jwt_service
        self._user_model = user_model

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials = await super().__call__(request)
        if credentials is None:
            return None

        request = cast(AuthenticatedRequest, request)

        payload = self._get_token_payload(token=credentials.credentials)
        request.state.jwt_payload = payload

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Token payload missing 'sub' field",
            )

        try:
            user = await self._user_model.objects.aget(id=user_id)  # type: ignore[attr-defined]
        except self._user_model.DoesNotExist as e:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="User not found",
            ) from e

        request.state.user = user

        return credentials

    def _get_token_payload(self, token: str) -> dict[str, Any]:
        try:
            return self._jwt_service.decode_token(token=token)
        except self._jwt_service.EXPIRED_SIGNATURE_ERROR as e:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Token has expired",
            ) from e
        except self._jwt_service.INVALID_TOKEN_ERROR as e:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid token",
            ) from e


class JWTAuthWithPermissions(JWTAuth):
    """JWT auth with optional is_staff/is_superuser checks."""

    def __init__(
        self,
        jwt_service: JWTService,
        user_model: type[AbstractBaseUser],
        *,
        require_staff: bool = False,
        require_superuser: bool = False,
    ) -> None:
        super().__init__(jwt_service=jwt_service, user_model=user_model)
        self._require_staff = require_staff
        self._require_superuser = require_superuser

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        credentials = await super().__call__(request)

        request = cast(AuthenticatedRequest, request)
        user = request.state.user

        if self._require_staff and not getattr(user, "is_staff", False):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Staff access required",
            )

        if self._require_superuser and not getattr(user, "is_superuser", False):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Superuser access required",
            )

        return credentials
