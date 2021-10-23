from django.contrib.auth.views import (LoginView, PasswordResetCompleteView,
                                       PasswordResetConfirmView,
                                       PasswordResetDoneView,
                                       PasswordResetView, LogoutView)
from django.urls import include, path
from rest_framework import routers

from . import views

urlpatterns = [
    path("", LoginView.as_view(template_name="login.html"), name="login"),
    path("login", views.LoginView.as_view(), name="login-url"),
    path("logout", LogoutView.as_view(), name="logout"),
    path(
        "password/reset_request",
        PasswordResetView.as_view(template_name="password_reset.html"),
        name="password-reset",
    ),
    path(
        "password/reset_request/done",
        PasswordResetDoneView.as_view(template_name="password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password/reset_change/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(template_name="password_change.html"),
        name="password_reset_confirm",
    ),
    path(
        "password/reset_change/done",
        PasswordResetCompleteView.as_view(template_name="password_change_done.html"),
        name="password_reset_done",
    ),
    path("redirect", views.logged_in_user_redirect, name="logged_in_user_redirect"),
    # SPA
    path("google_login", views.GoogleLoginView.as_view()),
    # path('logout', LogoutView.as_view()),
    # path('user', UserDetailsView.as_view()),
    # path('password/change', PasswordChangeView.as_view()),
]
