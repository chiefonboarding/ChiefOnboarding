from django.urls import include, path
from rest_framework import routers

from resources import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("resource", views.ResourceViewSet, "resource")

urlpatterns = [
    path("", include(router.urls)),
]
