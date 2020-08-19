from rest_framework import serializers
from .models import Organization, Tag, WelcomeMessage
from integrations.models import AccessToken
from misc.serializers import FileSerializer
from django.conf import settings


class BaseOrganizationSerializer(serializers.ModelSerializer):
    slack_key = serializers.SerializerMethodField(read_only=True)
    slack_account_key = serializers.SerializerMethodField(read_only=True)
    google_key = serializers.SerializerMethodField(read_only=True)
    google_login_key = serializers.SerializerMethodField(read_only=True)
    google_login_client_id = serializers.SerializerMethodField(read_only=True)
    logo = serializers.SerializerMethodField(read_only=True)
    base_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Organization
        fields = ('name', 'timezone', 'language', 'base_color', 'accent_color', 'credentials_login',
                  'google_login', 'slack_login', 'slack_key', 'slack_account_key', 'google_key', 'google_login_key',
                  'logo', 'google_login_client_id', 'base_url')

    def get_slack_key(self, obj):
        return AccessToken.objects.filter(integration=0, active=True).exists()

    def get_slack_account_key(self, obj):
        return AccessToken.objects.filter(integration=1, active=True).exists()

    def get_google_key(self, obj):
        return AccessToken.objects.filter(integration=2, active=True).exists()

    def get_google_login_key(self, obj):
        return AccessToken.objects.filter(integration=3, active=True).exists()

    def get_base_url(self, obj):
        return settings.BASE_URL

    def get_google_login_client_id(self, obj):
        if AccessToken.objects.filter(integration=3, active=True).exists():
            return AccessToken.objects.get(integration=3).client_id
        return ''

    def get_logo(self, obj):
        if obj.logo is None:
            return ''
        return obj.logo.get_url()


class DetailOrganizationSerializer(BaseOrganizationSerializer):
    logo = FileSerializer(read_only=True)

    class Meta:
        model = Organization
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('name',)


class WelcomeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelcomeMessage
        fields = '__all__'

