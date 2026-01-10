from dataclasses import dataclass
from datetime import timedelta


@dataclass(kw_only=True, frozen=True, slots=True)
class RefreshSessionServiceSettings:
    refresh_token_nbytes: int = 32
    refresh_token_ttl: timedelta = timedelta(days=30)
