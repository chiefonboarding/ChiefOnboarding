from django.urls import path

from . import views

app_name = "introductions"
urlpatterns = [
    path("introductions/", views.IntroductionListView.as_view(), name="list"),
    path("introductions/create", views.IntroductionCreateView.as_view(), name="create"),
    path("introductions/<int:pk>/edit", views.IntroductionUpdateView.as_view(), name="update"),
    path("introductions/<int:pk>/delete", views.IntroductionDeleteView.as_view(), name="delete"),
]
