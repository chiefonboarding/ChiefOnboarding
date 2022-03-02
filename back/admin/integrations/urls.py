from django.urls import path

from . import views

urlpatterns = [
    path("slack", views.SlackOAuthView.as_view()),
]
