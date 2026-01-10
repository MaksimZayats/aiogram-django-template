import inspect
from typing import Any

from pydantic import SecretBytes, SecretStr
from pydantic_settings import BaseSettings


class PydanticSettingsAdapter:
    # NOTE TO AI: this class will adapt pydantic settings to django settings
    # accept multiple pydantic settings and set them to django settings
    def adapt(self, *settings: BaseSettings) -> None:
        stack = inspect.stack()
        parent_frame = stack[1]

        for setting in settings:
            self._adapt(settings=setting, parent_frame=parent_frame)

    def _adapt(
        self,
        settings: BaseSettings,
        parent_frame: inspect.FrameInfo,
    ) -> None:
        for key, value in settings.model_dump().items():
            resolved_key = self._resolve_key(key)
            resolved_value = self._resolve_value(value)
            parent_frame.frame.f_locals[resolved_key] = resolved_value

    def _resolve_key(self, key: str) -> str:
        return key.upper()

    def _resolve_value(self, value: Any) -> Any:
        if isinstance(value, (SecretStr, SecretBytes)):
            return value.get_secret_value()

        return value
