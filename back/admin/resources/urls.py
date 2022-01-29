from django.urls import path

from . import views

app_name = "resources"
urlpatterns = [
    path("resources/", views.ResourceListView.as_view(), name="list"),
    path("resources/create", views.ResourceCreateView.as_view(), name="create"),
    path("resources/<int:pk>/edit", views.ResourceUpdateView.as_view(), name="update"),
    path(
        "resources/<int:pk>/delete", views.ResourceDeleteView.as_view(), name="delete"
    ),
]
