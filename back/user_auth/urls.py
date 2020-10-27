from django.urls import path, include
from rest_framework import routers
from . import views
from rest_auth.views import (
    LogoutView, UserDetailsView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView
)

urlpatterns = [
    path('login', views.LoginView.as_view(), name='login-url'),
    path('google_login', views.GoogleLoginView.as_view()),
    path('password/reset', PasswordResetView.as_view()),
    path('password/reset/confirm', PasswordResetConfirmView.as_view()),
    path('logout', LogoutView.as_view()),
    path('user', UserDetailsView.as_view()),
    path('password/change', PasswordChangeView.as_view()),
]