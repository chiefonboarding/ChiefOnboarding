from django.urls import path

from . import views

app_name = "preboarding"
urlpatterns = [
    path("preboarding/", views.PreboardingListView.as_view(), name="list"),
    path("preboarding/create", views.PreboardingCreateView.as_view(), name="create"),
    path("preboarding/<int:pk>/edit", views.PreboardingUpdateView.as_view(), name="update"),
    path("preboarding/<int:pk>/delete", views.PreboardingDeleteView.as_view(), name="delete"),
]
