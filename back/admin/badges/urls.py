from django.urls import path

from . import views

app_name = "badges"
urlpatterns = [
    path("", views.BadgeListView.as_view(), name="list"),
    path("create", views.BadgeCreateView.as_view(), name="create"),
    path("<int:pk>/edit", views.BadgeUpdateView.as_view(), name="update"),
    path("<int:pk>/delete", views.BadgeDeleteView.as_view(), name="delete"),
]
