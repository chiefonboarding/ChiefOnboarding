from django.urls import path

from . import views

app_name = "introductions"
urlpatterns = [
    path("", views.IntroductionListView.as_view(), name="list"),
    path("create/", views.IntroductionCreateView.as_view(), name="create"),
    path(
        "<int:pk>/edit/",
        views.IntroductionUpdateView.as_view(),
        name="update",
    ),
    path(
        "<int:pk>/delete/",
        views.IntroductionDeleteView.as_view(),
        name="delete",
    ),
    path(
        "<int:pk>/preview/",
        views.IntroductionColleaguePreviewView.as_view(),
        name="preview",
    ),
]
