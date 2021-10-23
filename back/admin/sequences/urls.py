from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("sequences", views.SequenceViewSet, "sequences")

urlpatterns = [
    path("", include(router.urls)),
    path("external_messages", views.SaveExternalMessage.as_view()),
    path("send_test_message/<int:id>", views.SendTestMessage.as_view()),
    path("sequence/admin_task", views.SaveAdminTask.as_view()),
]
