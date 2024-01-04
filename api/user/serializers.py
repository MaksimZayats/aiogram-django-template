from __future__ import annotations

from rest_framework import serializers

from api.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}  # noqa: RUF012
