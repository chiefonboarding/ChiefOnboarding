from django.urls import path, re_path
from allauth.account import views as allauth_views
from allauth.mfa import views as allauth_mfa_views

from . import views

urlpatterns = [
    # allauth urls
    path("", allauth_views.login, name="account_login"),
    path(
        "password/reset/", allauth_views.password_reset, name="account_reset_password"
    ),
    path(
        "password/reset/done/",
        allauth_views.password_reset_done,
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        allauth_views.password_reset_from_key,
        name="account_reset_password_from_key",
    ),
    path(
        "password/reset/key/done/",
        allauth_views.password_reset_from_key_done,
        name="account_reset_password_from_key_done",
    ),
    path("authenticate/", allauth_mfa_views.authenticate, name="mfa_authenticate"),
    path(
        "reauthenticate/", allauth_views.reauthenticate, name="account_reauthenticate"
    ),
    path("logout/", allauth_views.LogoutView.as_view(), name="logout"),
    path(
        "redirect/", views.LoginRedirectView.as_view(), name="logged_in_user_redirect"
    ),
    path("api/auth/oidc_login/", views.OIDCLoginView.as_view(), name="oidc_login"),
]
