from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel

from api.user.auth import default_auth

router = Router(tags=["user"])


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_staff: bool
    is_superuser: bool


@router.get("/v1/users/me", auth=default_auth)
async def get_current_user(request: HttpRequest) -> UserSchema:
    return UserSchema.model_validate(request.user, from_attributes=True)
