from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import BadgeSerializer
from .models import Badge


class BadgeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows badges to be created/updated/deleted.
    """
    serializer_class = BadgeSerializer
    queryset = Badge.objects.all()

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk):
        self.get_object().duplicate()
        return Response()