from django.urls import path

from . import views

app_name = "organization"
urlpatterns = [
    path("search/", views.SearchHXView.as_view(), name="search"),
    path("file", views.FileView.as_view(), name="create_file"),
    path("file/<int:id>", views.FileView.as_view(), name="file"),
    path("file/<int:id>/<uuid:uuid>/", views.FileView.as_view(), name="get_file"),
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notifications",
    ),
]
