from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("admin_tasks", views.AdminTaskViewSet, "admin_tasks")

urlpatterns = [
    path("", include(router.urls)),
]
