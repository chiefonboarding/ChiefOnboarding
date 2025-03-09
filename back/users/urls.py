from django.urls import include, path

from . import views

urlpatterns = [
    # allauth urls
    path("", views.CustomLoginView.as_view(), name="account_login"),
    # mocking this one, it's necessary for loading the login page, but we actually never
    # use it, so just loop it back to the login page out of safety.
    # TODO: Fix this
    # path("", allauth_views.login, name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path(
        "redirect/", views.LoginRedirectView.as_view(), name="logged_in_user_redirect"
    ),
]
