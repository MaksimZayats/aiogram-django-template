from pydantic import Field
from pydantic_settings import BaseSettings


class HTTPSettings(BaseSettings):
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    csrf_trusted_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])

    cors_allow_credentials: bool = True
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost"])
