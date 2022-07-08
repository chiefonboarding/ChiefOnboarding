from django.urls import path

from . import views

app_name = "preboarding"
urlpatterns = [
    path("", views.PreboardingListView.as_view(), name="list"),
    path("create", views.PreboardingCreateView.as_view(), name="create"),
    path(
        "<int:pk>/edit",
        views.PreboardingUpdateView.as_view(),
        name="update",
    ),
    path(
        "<int:pk>/delete",
        views.PreboardingDeleteView.as_view(),
        name="delete",
    ),
]
