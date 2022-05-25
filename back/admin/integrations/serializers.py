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
    url = serializers.CharField()
    name = serializers.CharField()
    type = serializers.ChoiceField(
        [
            ("multiple_choice", "Multiple choice"),
            ("choice", "Choice"),
            ("input", "Input field"),
        ]
    )
    items = serializers.CharField(required=False)
    data_from = serializers.CharField(required=False)
    choice_id = serializers.CharField()
    choice_name = serializers.CharField()


class ManifestExistSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    expected = serializers.CharField()
    method = serializers.ChoiceField(
        [
            ("HEAD", "HEAD"),
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
        ]
    )


class ManifestExecuteSerializer(ValidateMixin, serializers.Serializer):
    url = serializers.CharField()
    data = serializers.JSONField()
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


class ManifestSerializer(ValidateMixin, serializers.Serializer):
    form = ManifestFormSerializer(required=False, many=True)
    exists = ManifestExistSerializer(required=False)
    execute = ManifestExecuteSerializer(many=True)
    post_execute_notification = ManifestPostExecuteNotificationSerializer(
        many=True, required=False
    )
    initial_data_form = ManifestInitialDataFormSerializer(many=True, required=False)
    headers = serializers.JSONField(required=False)
