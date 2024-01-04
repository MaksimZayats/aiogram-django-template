from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request


class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:  # noqa: ARG002
        return cast(bool, request.user.is_staff)
