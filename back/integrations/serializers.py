from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import AccessToken, ScheduledAccess


class SlackTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccessToken
        fields = ('client_id', 'app_id', 'integration', 'client_secret', 'signing_secret', 'verification_token')


class GoogleAPITokenSerializer(serializers.ModelSerializer):
    one_time_auth_code = serializers.UUIDField(read_only=True)

    class Meta:
        model = AccessToken
        fields = ('integration', 'client_id', 'client_secret', 'redirect_url', 'one_time_auth_code')


class GoogleOAuthTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = AccessToken
        fields = ('client_id', 'client_secret', 'integration', 'redirect_url')


class ScheduledAccessSerializer(serializers.ModelSerializer):
    new_hire_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=get_user_model().objects.all()
    )

    class Meta:
        model = ScheduledAccess
        fields = ('new_hire_id', 'integration', 'status', 'integration', 'email')
