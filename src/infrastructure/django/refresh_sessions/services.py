import hashlib
import ipaddress
import secrets
from collections.abc import Mapping
from datetime import timedelta
from typing import NamedTuple, Protocol

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction
from django.utils import timezone
from pydantic_settings import BaseSettings

from infrastructure.django.refresh_sessions.models import BaseRefreshSession


class RequestProtocol(Protocol):
    """Protocol for request objects that can provide user agent and IP address."""

    @property
    def headers(self) -> Mapping[str, str]: ...

    @property
    def client(self) -> tuple[str, int] | None: ...


class RefreshSessionServiceSettings(BaseSettings):
    refresh_token_nbytes: int = 32
    refresh_token_ttl_days: int = 30
    num_proxies: int = 0

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


class RefreshSessionService:
    def __init__(
        self,
        settings: RefreshSessionServiceSettings,
        refresh_session_model: type[BaseRefreshSession],
    ) -> None:
        self._settings = settings
        self._refresh_session_model = refresh_session_model

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
            user_agent=self._get_user_agent(request),
            ip_address=self._get_ip_address(request),
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

    def _get_user_agent(self, request: RequestProtocol) -> str:
        return request.headers.get("user-agent", "")

    def _get_ip_address(self, request: RequestProtocol) -> str | None:
        xff = request.headers.get("x-forwarded-for")
        client = request.client
        remote_address = client[0] if client else None

        if self._settings.num_proxies == 0 or xff is None:
            # Validate that remote_address is a valid IP, otherwise return None
            if remote_address and self._is_valid_ip(remote_address):
                return remote_address
            return None

        addresses = xff.split(",")
        client_address = addresses[-min(self._settings.num_proxies, len(addresses))]
        return client_address.strip()

    def _is_valid_ip(self, address: str) -> bool:
        try:
            ipaddress.ip_address(address)
        except ValueError:
            return False
        else:
            return True
