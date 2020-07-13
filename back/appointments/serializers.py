from rest_framework import serializers
from .models import Appointment
from misc.fields import ContentField


class AppointmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    content = ContentField()

    class Meta:
        model = Appointment
        fields = '__all__'
