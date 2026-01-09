from http import HTTPStatus

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from api.infrastructure.django.auth import JWTAuth
from api.infrastructure.django.controller import Controller
from api.infrastructure.jwt.service import JWTService
from api.user.models import User


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
    ) -> None:
        self._jwt_service = jwt_service

    def register_routes(self, router: Router) -> None:
        router.add_api_operation(
            path="/v1/users/me/token",
            methods=["POST"],
            view_func=self.issue_user_token,
            auth=None,
        )

        router.add_api_operation(
            path="/v1/users/me/token/refresh",
            methods=["POST"],
            view_func=self.refresh_user_token,
            auth=None,
        )

    def issue_user_token(
        self,
        request: HttpRequest,
        body: IssueTokenRequestSchema,
    ) -> TokenResponseSchema:
        user = User.objects.filter(username=body.username).first()
        if user is None or not user.check_password(body.password):
            raise HttpError(
                status_code=HTTPStatus.UNAUTHORIZED,
                message="Invalid username or password",
            )

        access_token = self._jwt_service.issue_access_token(user_id=user.pk)
        refresh_token = self._jwt_service.issue_refresh_token()

        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_user_token(
        self,
        request: HttpRequest,
        body: IssueTokenRequestSchema,
    ) -> TokenResponseSchema:
        pass


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

    def register_routes(self, router: Router) -> None:
        router.add_api_operation(
            path="/v1/users/me",
            methods=["GET"],
            view_func=self.get_current_user,
            auth=self._auth,
        )

    def get_current_user(
        self,
        request: HttpRequest,
    ) -> UserSchema:
        return UserSchema.model_validate(request.user, from_attributes=True)
