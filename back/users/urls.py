from allauth.account import views as allauth_views
from django.urls import include, path

from . import views

urlpatterns = [
    # allauth urls
    path("", allauth_views.login, name="account_login"),
    # mocking "signup", it's necessary for loading the login page, but we actually never
    # use it, so just loop it back to the login page out of safety.
    path("", allauth_views.login, name="account_signup"),
    path(
        "redirect/", views.LoginRedirectView.as_view(), name="logged_in_user_redirect"
    ),
    # allauth
    path("accounts/", include("allauth.urls")),
]
