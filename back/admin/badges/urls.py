from django.urls import path

from . import views

app_name = "badges"
urlpatterns = [
    path("badges/", views.BadgeListView.as_view(), name="list"),
    path("badges/create", views.BadgeCreateView.as_view(), name="create"),
    path("badges/<int:pk>/edit", views.BadgeUpdateView.as_view(), name="update"),
    path("badges/<int:pk>/delete", views.BadgeDeleteView.as_view(), name="delete"),
]
