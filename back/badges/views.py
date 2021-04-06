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
    queryset = Badge.objects.select_related('image').prefetch_related('content').all()

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk):
        obj = self.get_object()
        obj.pk = None
        obj.save()
        for i in Badge.objects.get(pk=pk).content.all():
            obj.content.add(i)
        return Response()
