import logging
from http import HTTPStatus
from typing import Annotated, NoReturn, cast

from annotated_types import Len
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel, EmailStr

from core.user.models import User
from infrastructure.delivery.controllers import Controller
from infrastructure.django.auth import JWTAuth
from infrastructure.django.refresh_sessions.services import (
    ExpiredRefreshTokenError,
    InvalidRefreshTokenError,
    RefreshSessionService,
    RefreshTokenError,
)
from infrastructure.jwt.services import JWTService
from tasks.registry import TasksRegistry

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
        jwt_service: JWTService,
        refresh_token_service: RefreshSessionService,
        jwt_auth: JWTAuth,
        tasks: TasksRegistry,
    ) -> None:
        self._jwt_service = jwt_service
        self._refresh_token_service = refresh_token_service
        self._jwt_auth = jwt_auth
        self._tasks_registry = tasks

    def register(self, registry: Router) -> None:
        print(f"{self.__class__.__name__} registered!")
        registry.add_api_operation(
            path="/v1/users/me/token",
            methods=["POST"],
            view_func=self.issue_user_token,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/users/me/token/refresh",
            methods=["POST"],
            view_func=self.refresh_user_token,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/users/me/token/revoke",
            methods=["POST"],
            view_func=self.revoke_refresh_token,
            auth=self._jwt_auth,
        )

    def issue_user_token(
        self,
        request: HttpRequest,
        body: IssueTokenRequestSchema,
    ) -> TokenResponseSchema:
        r = self._tasks_registry.ping.delay().get(timeout=10)
        logger.info("Ping task result: %s", r)

        user = User.objects.filter(username=body.username).first()
        if user is None or not user.check_password(body.password):
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
        request: HttpRequest,
        body: RefreshTokenRequestSchema,
    ) -> None:
        self._refresh_token_service.revoke_refresh_token(
            refresh_token=body.refresh_token,
            user=cast(User, request.user),
        )

    def handle_exception(self, exception: Exception) -> NoReturn:
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

        raise exception


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
        auth: JWTAuth,
    ) -> None:
        self._auth = auth

    def register(self, registry: Router) -> None:
        registry.add_api_operation(
            path="/v1/users/",
            methods=["POST"],
            view_func=self.create_user,
            auth=None,
        )

        registry.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._auth,
        )

    def create_user(
        self,
        request: HttpRequest,
        request_body: CreateUserRequestSchema,
    ) -> UserSchema:
        try:
            validate_password(request_body.password)
        except ValidationError as exc:
            raise HttpError(
                status_code=HTTPStatus.BAD_REQUEST,
                message=str(exc.message),
            ) from exc

        if User.objects.filter(username=request_body.username).exists():
            raise HttpError(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Username already exists",
            )

        if User.objects.filter(email=request_body.email).exists():
            raise HttpError(
                status_code=HTTPStatus.BAD_REQUEST,
                message="Email already exists",
            )

        user = User.objects.create_user(
            username=request_body.username,
            email=str(request_body.email),
            first_name=request_body.first_name,
            last_name=request_body.last_name,
            password=request_body.password,
        )

        return UserSchema.model_validate(user, from_attributes=True)

    def get_current_user(
        self,
        request: HttpRequest,
    ) -> UserSchema:
        return UserSchema.model_validate(request.user, from_attributes=True)
