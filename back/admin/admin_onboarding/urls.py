from django.urls import path

from . import views

app_name = "admin_onboarding"
urlpatterns = [
    path(
        "complete/",
        views.AdminOnboardingCompleteView.as_view(),
        name="complete",
    ),
    path(
        "content/",
        views.AdminOnboardingContentView.as_view(),
        name="content",
    ),
]
