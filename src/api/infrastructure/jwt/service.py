from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


@dataclass(kw_only=True, frozen=True, slots=True)
class JWTServiceSettings:
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire: timedelta = timedelta(minutes=15)


class JWTService:
    EXPIRED_SIGNATURE_ERROR = jwt.ExpiredSignatureError
    INVALID_TOKEN_ERROR = jwt.InvalidTokenError

    def __init__(self, settings: JWTServiceSettings) -> None:
        self._settings = settings

    def issue_access_token(
        self,
        user_id: Any,
        **payload_kwargs: Any,
    ) -> str:
        iat = datetime.now(tz=UTC)
        payload = {
            "sub": str(user_id),
            "exp": iat + self._settings.access_token_expire,
            "iat": iat,
            **payload_kwargs,
        }

        return jwt.encode(
            payload=payload,
            key=self._settings.secret_key,
            algorithm=self._settings.algorithm,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            jwt=token,
            key=self._settings.secret_key,
            algorithms=[self._settings.algorithm],
        )
