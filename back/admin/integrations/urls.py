from django.urls import path

from . import views

urlpatterns = [
    path("google_login", views.GoogleLoginTokenCreateView.as_view()),
    path("google_token", views.GoogleAddTokenView.as_view()),
    path("slack", views.SlackOAuthView.as_view()),
    path("slack/oauth", views.SlackCreateAccountView.as_view()),
]
