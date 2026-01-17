import hashlib
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import NamedTuple

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone
from pydantic_settings import BaseSettings

from infrastructure.delivery.request import RequestInfoService, RequestProtocol
from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class RefreshSessionServiceSettings(BaseSettings):
    refresh_token_nbytes: int = 32
    refresh_token_ttl_days: int = 30

    @property
    def refresh_token_ttl(self) -> timedelta:
        return timedelta(days=self.refresh_token_ttl_days)


class RefreshSessionResult(NamedTuple):
    refresh_token: str
    session: BaseRefreshSession


class RefreshTokenError(Exception):
    pass


class InvalidRefreshTokenError(RefreshTokenError):
    pass


class ExpiredRefreshTokenError(RefreshTokenError):
    pass


@dataclass
class RefreshSessionService:
    _settings: RefreshSessionServiceSettings
    _refresh_session_model: type[BaseRefreshSession]
    _request_info_service: RequestInfoService

    def create_refresh_session(
        self,
        request: RequestProtocol,
        user: AbstractBaseUser,
    ) -> RefreshSessionResult:
        refresh_token = self._issue_refresh_token()
        refresh_token_hash = self._hash_refresh_token(refresh_token)

        session = self._refresh_session_model.objects.create(  # type: ignore[attr-defined]
            user=user,
            refresh_token_hash=refresh_token_hash,
            user_agent=self._request_info_service.get_user_agent(request),
            ip_address=self._request_info_service.get_user_ip(request),
            expires_at=timezone.now() + self._settings.refresh_token_ttl,
        )

        return RefreshSessionResult(refresh_token=refresh_token, session=session)

    @transaction.atomic
    def rotate_refresh_token(self, refresh_token: str) -> RefreshSessionResult:
        session = self._get_refresh_session(refresh_token)

        new_refresh_token = self._issue_refresh_token()
        session.refresh_token_hash = self._hash_refresh_token(new_refresh_token)
        session.rotation_counter += 1
        session.last_used_at = timezone.now()
        session.save(
            update_fields=[
                "refresh_token_hash",
                "rotation_counter",
                "last_used_at",
            ],
        )

        return RefreshSessionResult(refresh_token=new_refresh_token, session=session)

    @transaction.atomic
    def revoke_refresh_token(
        self,
        refresh_token: str,
        user: AbstractBaseUser,
    ) -> None:
        session = self._get_refresh_session(refresh_token)
        if session.user.pk != user.pk:
            raise InvalidRefreshTokenError

        session.revoked_at = timezone.now()
        session.save(update_fields=["revoked_at"])

    def _issue_refresh_token(self) -> str:
        return secrets.token_urlsafe(nbytes=self._settings.refresh_token_nbytes)

    def _hash_refresh_token(self, refresh_token: str) -> str:
        return hashlib.sha256(refresh_token.encode()).hexdigest()

    def _get_refresh_session(
        self,
        refresh_token: str,
    ) -> BaseRefreshSession:
        try:
            session = self._refresh_session_model.objects.get(  # type: ignore[attr-defined]
                refresh_token_hash=self._hash_refresh_token(refresh_token),
            )
        except self._refresh_session_model.DoesNotExist as e:
            raise InvalidRefreshTokenError from e

        if not session.is_active:
            raise ExpiredRefreshTokenError

        return session
