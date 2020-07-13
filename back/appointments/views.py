from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    queryset = Appointment.templates.all().order_by('id')

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk):
        self.get_object().duplicate()
        return Response()
