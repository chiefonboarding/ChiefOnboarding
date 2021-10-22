from django.urls import include, path
from rest_framework import routers

from . import views

urlpatterns = [
    path("", views.OrgView.as_view()),
    path("detail", views.OrgDetailView.as_view()),
    path("CSRF_token", views.CSRFTokenView.as_view()),
    path("tags", views.TagView.as_view()),
    path("export", views.ExportView.as_view()),
    path("welcome_message", views.WelcomeMessageView.as_view()),
    path("file", views.FileView.as_view()),
    path("file/<int:id>", views.FileView.as_view()),
    path("logo/<int:id>", views.LogoView.as_view()),
    path("file/<int:id>/<uuid:uuid>", views.FileView.as_view()),
]
