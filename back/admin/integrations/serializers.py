from django.core.exceptions import ValidationError
from django_q.models import validate_cron
from rest_framework import serializers


# Credit: https://stackoverflow.com/a/42432240
class ValidateMixin:
    def validate(self, data):
        if hasattr(self, "initial_data"):
            unknown_keys = set(self.initial_data.keys()) - set(self.fields.keys())
            if unknown_keys:
                raise ValidationError("Got unknown fields: {}".format(unknown_keys))
        return data


class ManifestFormSerializer(ValidateMixin, serializers.Serializer):
    id = serializers.CharField()
    url = serializers.CharField(required=False)
    name = serializers.CharField()
    type = serializers.ChoiceField(
        [
            ("multiple_choice", "Multiple choice"),
            ("choice", "Choice"),
            ("input", "Input field"),
            ("generate", "Generate random text"),
        ]
    )
    items = serializers.JSONField(required=False)
    data_from = serializers.CharField(required=False)
    choice_value = serializers.CharField(required=False)
    choice_name = serializers.CharField(required=False)


class ManifestConditionSerializer(ValidateMixin, serializers.Serializer):
    response_notation = serializers.CharField()
    value = serializers.CharField()


class ManifestPollingSerializer(ValidateMixin, serializers.Serializer):
    interval = serializers.IntegerField(min_value=1, max_value=3600)
    amount = serializers.IntegerField(min_value=1, max_value=100)


class ManifestExistSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    expected = serializers.CharField()
    fail_when_4xx_response_code = serializers.BooleanField(required=False)
    method = serializers.ChoiceField(
        [
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )


class ManifestExecuteSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    headers = serializers.DictField(child=serializers.CharField(), default=dict)
    store_data = serializers.DictField(child=serializers.CharField(), default=dict)
    method = serializers.ChoiceField(
        [
            ("HEAD", "HEAD"),
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )
    files = serializers.DictField(child=serializers.CharField(), default=dict)
    save_as_file = serializers.CharField(required=False)
    polling = ManifestPollingSerializer(required=False)
    continue_if = ManifestConditionSerializer(required=False)

    def validate(self, data):
        # Check that if polling has been filled, that continue_if is also filled
        polling = data.get("polling", False)
        continue_if = data.get("continue_if", False)
        if polling and not continue_if:
            raise serializers.ValidationError(
                "continue_if must be filled if you use polling"
            )
        return data


class ManifestRevokeSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    headers = serializers.DictField(child=serializers.CharField(), default=dict)
    method = serializers.ChoiceField(
        [
            ("HEAD", "HEAD"),
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )


class ManifestPostExecuteNotificationSerializer(ValidateMixin, serializers.Serializer):
    type = serializers.ChoiceField(
        [
            ("email", "Email message"),
            ("text", "Text message"),
        ]
    )
    to = serializers.CharField()
    subject = serializers.CharField()
    message = serializers.CharField()


class ManifestInitialDataFormSerializer(ValidateMixin, serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    secret = serializers.BooleanField(default=True)
    description = serializers.CharField()


class ManifestExtraUserInfoFormSerializer(ValidateMixin, serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()


class ManifestOauthSerializer(ValidateMixin, serializers.Serializer):
    authenticate_url = serializers.CharField()
    access_token = ManifestExecuteSerializer(required=True)
    refresh = ManifestExecuteSerializer(required=True)
    without_code = serializers.BooleanField(required=False)


class WebhookManifestSerializer(ValidateMixin, serializers.Serializer):
    form = ManifestFormSerializer(required=False, many=True)
    exists = ManifestExistSerializer(required=False)
    revoke = ManifestRevokeSerializer(required=False, many=True)
    execute = ManifestExecuteSerializer(many=True)
    post_execute_notification = ManifestPostExecuteNotificationSerializer(
        many=True, required=False
    )
    initial_data_form = ManifestInitialDataFormSerializer(many=True, required=False)
    extra_user_info = ManifestExtraUserInfoFormSerializer(many=True, required=False)
    headers = serializers.DictField(child=serializers.CharField(), default=dict)
    oauth = ManifestOauthSerializer(required=False)


class SyncUsersManifestSerializer(ValidateMixin, serializers.Serializer):
    data_from = serializers.CharField(required=False)
    data_structure = serializers.DictField(child=serializers.CharField())
    execute = ManifestExecuteSerializer(many=True)
    next_page_token_from = serializers.CharField(required=False)
    next_page = serializers.CharField(required=False)
    next_page_from = serializers.CharField(required=False)
    schedule = serializers.CharField(required=False, validators=[validate_cron])
    action = serializers.ChoiceField([("create", "create"), ("update", "update")])
    amount_pages_to_fetch = serializers.IntegerField(required=False)
    initial_data_form = ManifestInitialDataFormSerializer(many=True, required=False)
    headers = serializers.DictField(child=serializers.CharField(), default=dict)
    oauth = ManifestOauthSerializer(required=False)
