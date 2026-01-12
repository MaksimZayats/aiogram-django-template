from django.contrib.auth.models import AbstractUser

from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class User(AbstractUser):
    pass


class RefreshSession(BaseRefreshSession):
    pass
