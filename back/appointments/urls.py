from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("appointment", views.AppointmentViewSet, "appointment")

urlpatterns = [
    path("", include(router.urls)),
]
