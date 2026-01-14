import logging
from http import HTTPStatus
from typing import Annotated, Any

from annotated_types import Len
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from ninja.throttling import AnonRateThrottle, AuthRateThrottle
from pydantic import BaseModel, EmailStr

from core.user.services import UserService
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import AuthenticatedHttpRequest, JWTAuth
from infrastructure.django.refresh_sessions.services import (
    ExpiredRefreshTokenError,
    InvalidRefreshTokenError,
    RefreshSessionService,
    RefreshTokenError,
)
from infrastructure.jwt.services import JWTService

logger = logging.getLogger(__name__)


class IssueTokenRequestSchema(BaseModel):
    username: str
    password: str


class RefreshTokenRequestSchema(BaseModel):
    refresh_token: str


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str


class UserTokenController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        user_service: UserService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._user_service = user_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/me/token",
            methods=["POST"],
            view_func=self.issue_user_token,
            auth=None,
            throttle=AnonRateThrottle(rate="5/min"),
        )

        registry.add_api_operation(
            path="/v1/users/me/token/refresh",
            methods=["POST"],
            view_func=self.refresh_user_token,
            auth=None,
            throttle=AnonRateThrottle(rate="5/min"),
        )

        registry.add_api_operation(
            path="/v1/users/me/token/revoke",
            methods=["POST"],
            view_func=self.revoke_refresh_token,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="5/min"),
        )

    def issue_user_token(
        self,
        request: HttpRequest,
        body: IssueTokenRequestSchema,
    ) -> TokenResponseSchema:
        user = self._user_service.get_user_by_username_and_password(
            username=body.username,
            password=body.password,
        )

        if user is None:
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid username or password",
            )

        access_token = self._jwt_service.issue_access_token(user_id=user.pk)
        refresh_session = self._refresh_token_service.create_refresh_session(
            request=request,
            user=user,
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_session.refresh_token,
        )

    def refresh_user_token(
        self,
        request: HttpRequest,
        body: RefreshTokenRequestSchema,
    ) -> TokenResponseSchema:
        rotated_session = self._refresh_token_service.rotate_refresh_token(
            refresh_token=body.refresh_token,
        )

        access_token = self._jwt_service.issue_access_token(
            user_id=rotated_session.session.user.pk,
        )

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=rotated_session.refresh_token,
        )

    def revoke_refresh_token(
        self,
        request: AuthenticatedHttpRequest,
        body: RefreshTokenRequestSchema,
    ) -> None:
        self._refresh_token_service.revoke_refresh_token(
            refresh_token=body.refresh_token,
            user=request.user,
        )

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, InvalidRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid refresh token",
            ) from exception

        if isinstance(exception, ExpiredRefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token expired or revoked",
            ) from exception

        if isinstance(exception, RefreshTokenError):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Refresh token error",
            ) from exception

        return super().handle_exception(exception)


class CreateUserRequestSchema(BaseModel):
    email: EmailStr
    username: Annotated[str, Len(max_length=150)]
    first_name: Annotated[str, Len(max_length=150)]
    last_name: Annotated[str, Len(max_length=150)]
    password: Annotated[str, Len(max_length=128)]


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_superuser: bool


class UserController(Controller):
    def __init__(
        self,
        jwt_auth: JWTAuth,
        user_service: UserService,
    ) -> None:
        self._jwt_auth = jwt_auth
        self._user_service = user_service

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/",
            methods=["POST"],
            view_func=self.create_user,
            auth=None,
            throttle=AnonRateThrottle(rate="30/min"),
        )

        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._jwt_auth,
            throttle=AuthRateThrottle(rate="30/min"),
        )

    def create_user(
        self,
        request: HttpRequest,
        request_body: CreateUserRequestSchema,
    ) -> UserSchema:
        is_valid_password = self._user_service.is_valid_password(
            password=request_body.password,
            username=request_body.username,
            email=str(request_body.email),
            first_name=request_body.first_name,
            last_name=request_body.last_name,
        )

        if not is_valid_password:
            raise HttpError(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Password does not meet the strength requirements",
            )

        existing_user = self._user_service.get_user_by_username_or_email(
            username=request_body.username,
            email=str(request_body.email),
        )

        if existing_user is not None:
            raise HttpError(
                status_code=HTTPStatus.CONFLICT,
                message="A user with the given username or email already exists",
            )

        user = self._user_service.create_user(
            username=request_body.username,
            email=str(request_body.email),
            first_name=request_body.first_name,
            last_name=request_body.last_name,
            password=request_body.password,
        )

        return UserSchema.model_validate(user, from_attributes=True)

    def get_current_user(
        self,
        request: AuthenticatedHttpRequest,
    ) -> UserSchema:
        return UserSchema.model_validate(request.user, from_attributes=True)
