from django.urls import include, path
from rest_framework import routers

from to_do import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("to_do", views.ToDoViewSet, "to_do")

urlpatterns = [
    path("", include(router.urls)),
]
