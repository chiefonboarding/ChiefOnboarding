from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("preboarding", views.PreboardingViewSet, "preboarding")

urlpatterns = [
    path("", include(router.urls)),
]
