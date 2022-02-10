from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AccessToken


class SlackTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = (
            "client_id",
            "app_id",
            "integration",
            "client_secret",
            "signing_secret",
            "verification_token",
        )


class GoogleAPITokenSerializer(serializers.ModelSerializer):
    one_time_auth_code = serializers.UUIDField(read_only=True)

    class Meta:
        model = AccessToken
        fields = (
            "integration",
            "client_id",
            "client_secret",
            "redirect_url",
            "one_time_auth_code",
        )


class GoogleOAuthTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessToken
        fields = ("client_id", "client_secret", "integration", "redirect_url")
