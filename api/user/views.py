from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.common.routers import CustomViewRouter
from api.user import serializers
from api.user.models import User
from api.user.permissions import IsStaffPermission

if TYPE_CHECKING:
    from rest_framework.request import Request

router = CustomViewRouter()

logger = logging.getLogger(__name__)


@router.register(r"users/me/", name="users")
class MyUserView(GenericAPIView):
    serializer_class = serializers.UserSerializer

    def get(self, request: Request) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@router.register(r"users", name="users")
class UserViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()
    permission_classes = (IsStaffPermission,)
