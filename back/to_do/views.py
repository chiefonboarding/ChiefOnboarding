
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ToDo
from .serializers import ToDoSerializer


class ToDoViewSet(viewsets.ModelViewSet):
    serializer_class = ToDoSerializer

    def get_queryset(self):
        if self.action == 'list':
            return ToDo.templates.all().order_by('id')
        return ToDo.objects.all().order_by('id')

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk):
        self.get_object().duplicate()
        return Response()
