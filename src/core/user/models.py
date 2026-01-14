from django.contrib.auth.models import AbstractUser

from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class User(AbstractUser):
    def __str__(self) -> str:
        return f"User(id={self.pk}, username={self.username})"


class RefreshSession(BaseRefreshSession):
    pass
