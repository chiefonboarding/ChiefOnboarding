from django.conf import settings
from rest_framework import serializers

from admin.integrations.models import AccessToken
from admin.sequences.models import Sequence
from misc.serializers import FileSerializer

from .models import Organization, Tag, WelcomeMessage


class BaseOrganizationSerializer(serializers.ModelSerializer):
    slack_key = serializers.SerializerMethodField(read_only=True)
    slack_account_key = serializers.SerializerMethodField(read_only=True)
    google_key = serializers.SerializerMethodField(read_only=True)
    google_login_key = serializers.SerializerMethodField(read_only=True)
    google_login_client_id = serializers.SerializerMethodField(read_only=True)
    logo = serializers.SerializerMethodField(read_only=True)
    base_url = serializers.SerializerMethodField(read_only=True)
    auto_add_sequence = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Organization
        fields = (
            "name",
            "timezone",
            "language",
            "base_color",
            "accent_color",
            "credentials_login",
            "google_login",
            "slack_login",
            "slack_key",
            "slack_account_key",
            "google_key",
            "google_login_key",
            "logo",
            "google_login_client_id",
            "base_url",
            "auto_create_user",
            "create_new_hire_without_confirm",
            "slack_confirm_person",
            "auto_add_sequence",
        )

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
        return ""

    def get_auto_add_sequence(self, obj):
        return Sequence.objects.filter(auto_add=True).values_list("id", flat=True)

    def get_logo(self, obj):
        if obj.logo is None:
            return ""
        return obj.logo.get_url()


class DetailOrganizationSerializer(BaseOrganizationSerializer):
    logo = FileSerializer(read_only=True)

    class Meta:
        model = Organization
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)


class WelcomeMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WelcomeMessage
        fields = "__all__"


class ExportSerializer(serializers.Serializer):
    export_model = serializers.CharField(max_length=200)

    def validate_export_model(self, value):
        options = [
            "preboarding",
            "badges",
            "to_do",
            "resources",
            "introductions",
            "sequences",
            "users",
            "admin_tasks",
            "appointments",
        ]
        if value not in options:
            raise serializers.ValidationError("Not a valid option")
        return value
