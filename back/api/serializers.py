from rest_framework import serializers

from admin.sequences.models import Sequence
from users.models import User
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
    sequences = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate_sequences(self, value):
        if Sequence.objects.filter(pk__in=value).count() != len(value):
            raise serializers.ValidationError("Not all sequence ids are valid.")
        return value

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "start_day",
            "role",
            "email",
            "position",
            "phone",
            "buddy",
            "manager",
            "message",
            "linkedin",
            "facebook",
            "twitter",
            "timezone",
            "language",
            "sequences",
        ]


class UserOffboardingSerializer(serializers.Serializer):
    termination_date = serializers.DateField()
    sequences = serializers.ListField(child=serializers.IntegerField(), required=False)
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.exclude(role=User.Role.ADMIN)
    )

    def validate_termination_date(self, value):
        # date must be in the future
        if value < timezone.now().date():
            raise serializers.ValidationError("You cannot set an offboarding date in the past.")
        return value

    def validate_sequences(self, value):
        if Sequence.objects.filter(category=Sequence.Category.OFFBOARDING, pk__in=value).count() != len(value):
            raise serializers.ValidationError("Not all sequence ids are valid.")
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email"]


class SequenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sequence
        fields = ["id", "name"]
