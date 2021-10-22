from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Preboarding
from .serializers import PreboardingSerializer


class PreboardingViewSet(viewsets.ModelViewSet):
    serializer_class = PreboardingSerializer
    queryset = Preboarding.templates.all().order_by("id")

    @action(detail=True, methods=["post"])
    def duplicate(self, request, pk):
        obj = self.get_object()
        obj.pk = None
        obj.save()
        for i in Preboarding.objects.get(pk=pk).content.all():
            obj.content.add(i)
        return Response()
