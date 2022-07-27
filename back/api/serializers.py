import pytz
from rest_framework import serializers

from admin.sequences.models import Sequence
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    sequences = serializers.MultipleChoiceField(choices=[])
    timezone = serializers.MultipleChoiceField(
        choices=[(x, x) for x in pytz.common_timezones]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sequences"].choices = [
            (s.id, s.name) for s in Sequence.objects.all()
        ]

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "start_day",
            "email",
            "position",
            "phone",
            "message",
            "linkedin",
            "facebook",
            "twitter",
            "timezone",
            "language",
        ]


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = ["id", "name"]
