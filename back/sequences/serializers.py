from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from appointments.serializers import AppointmentSerializer
from badges.serializers import BadgeSerializer
from introductions.serializers import IntroductionSerializer
from misc.fields import ContentField
from preboarding.serializers import PreboardingSerializer
from resources.serializers import ResourceSerializer
from to_do.models import ToDo
from to_do.serializers import ToDoSerializer

from .models import Condition, ExternalMessage, PendingAdminTask, Sequence


class SeqEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "full_name",
            "slack_user_id",
        )


class SequenceListSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default="sequence")

    class Meta:
        model = Sequence
        fields = ("id", "name", "search_type", "auto_add")


class ExternalMessageSerializer(serializers.ModelSerializer):
    send_to = PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(), allow_null=True
    )
    content_json = ContentField()

    class Meta:
        model = ExternalMessage
        fields = "__all__"


class PendingAdminTaskSerializer(serializers.ModelSerializer):
    assigned_to = SeqEmployeeSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source="assigned_to", queryset=get_user_model().objects.all()
    )
    date = serializers.DateTimeField(required=False, allow_null=True)
    slack_user = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False)
    comment = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = PendingAdminTask
        fields = "__all__"


class ConditionSerializer(serializers.ModelSerializer):
    condition_to_do = ToDoSerializer(many=True, read_only=True)
    to_do = ToDoSerializer(many=True)
    badges = BadgeSerializer(many=True)
    resources = ResourceSerializer(many=True)
    admin_tasks = PendingAdminTaskSerializer(many=True)
    external_messages = ExternalMessageSerializer(many=True)
    introductions = IntroductionSerializer(many=True)

    class Meta:
        model = Condition
        fields = "__all__"


class SequenceSerializer(serializers.ModelSerializer):
    search_type = serializers.CharField(default="sequence", read_only=True)
    preboarding = PreboardingSerializer(many=True)
    to_do = ToDoSerializer(many=True)
    resources = ResourceSerializer(many=True)
    appointments = AppointmentSerializer(many=True)

    conditions = ConditionSerializer(many=True)

    class Meta:
        model = Sequence
        fields = "__all__"
