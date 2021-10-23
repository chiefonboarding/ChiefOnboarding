from rest_framework import serializers

from misc.fields import ContentField

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    content = ContentField()

    class Meta:
        model = Appointment
        fields = "__all__"
