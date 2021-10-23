from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("access", views.AccessViewSet, "access")


urlpatterns = [
    path("", include(router.urls)),
    path("slack_token", views.SlackTokenCreateView.as_view()),
    path("google", views.GoogleTokenCreateView.as_view()),
    path("google_login", views.GoogleLoginTokenCreateView.as_view()),
    path("google_token", views.GoogleAddTokenView.as_view()),
    path("slack", views.SlackOAuthView.as_view()),
    path("slack/oauth", views.SlackCreateAccountView.as_view()),
    path("token/<int:id>", views.TokenRemoveView.as_view()),
]
