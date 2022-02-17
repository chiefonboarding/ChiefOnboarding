from django.urls import path

from . import views

app_name = "organization"
urlpatterns = [
    path("file", views.FileView.as_view()),
    path("file/<int:id>", views.FileView.as_view()),
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notifications",
    ),
]
