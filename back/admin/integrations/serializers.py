from django.core.exceptions import ValidationError
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


class ManifestPollingUntilSerializer(ValidateMixin, serializers.Serializer):
    first_argument = serializers.CharField()
    second_argument = serializers.CharField()


class ManifestPollingSerializer(ValidateMixin, serializers.Serializer):
    interval = serializers.IntegerField(required=False)
    amount = serializers.IntegerField(required=False)
    until = ManifestPollingUntilSerializer()


class ManifestExistSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    expected = serializers.CharField()
    fail_when_4xx_response_code = serializers.BooleanField(required=False)
    method = serializers.ChoiceField(
        [
            ("HEAD", "HEAD"),
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )
    polling = ManifestPollingSerializer(required=False)


class ManifestExecuteSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    data = serializers.JSONField(required=False, default=dict)
    headers = serializers.JSONField(required=False, default=dict)
    store_data = serializers.DictField(child=serializers.CharField(), default=dict)
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
    type = serializers.ChoiceField(
        [
            ("generate", "Generate secret"),
        ],
        required=False,
    )
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


class ManifestSerializer(ValidateMixin, serializers.Serializer):
    type = serializers.ChoiceField(
        [
            ("import_users", "imports users from endpoint"),
        ],
        required=False,
    )
    form = ManifestFormSerializer(required=False, many=True)
    data_from = serializers.CharField(required=False)
    data_structure = serializers.JSONField(required=False)
    exists = ManifestExistSerializer(required=False)
    execute = ManifestExecuteSerializer(many=True)
    next_page_token_from = serializers.CharField(required=False)
    next_page = serializers.CharField(required=False)
    next_page_from = serializers.CharField(required=False)
    amount_pages_to_fetch = serializers.IntegerField(required=False)
    post_execute_notification = ManifestPostExecuteNotificationSerializer(
        many=True, required=False
    )
    initial_data_form = ManifestInitialDataFormSerializer(many=True, required=False)
    extra_user_info = ManifestExtraUserInfoFormSerializer(many=True, required=False)
    headers = serializers.JSONField(required=False)
    oauth = ManifestOauthSerializer(required=False)
