from django.urls import include, path
from rest_framework import routers

from notes import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("notes", views.NoteViewSet, "notes")

urlpatterns = [
    path("", include(router.urls)),
]
