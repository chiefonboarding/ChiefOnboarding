from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Introduction
from .serializers import IntroductionSerializer


class IntroductionViewSet(viewsets.ModelViewSet):
    serializer_class = IntroductionSerializer
    queryset = Introduction.objects.all().select_related('intro_person').order_by('id')
