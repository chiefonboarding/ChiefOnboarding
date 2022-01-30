from django.urls import path

from . import views

app_name = "appointments"
urlpatterns = [
    path("", views.AppointmentListView.as_view(), name="list"),
    path("create", views.AppointmentCreateView.as_view(), name="create"),
    path(
        "<int:pk>/edit",
        views.AppointmentUpdateView.as_view(),
        name="update",
    ),
    path(
        "<int:pk>/delete",
        views.AppointmentDeleteView.as_view(),
        name="delete",
    ),
]
