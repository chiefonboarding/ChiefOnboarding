from django.urls import path

from . import views

app_name = "settings"
urlpatterns = [
    path("general/", views.OrganizationGeneralUpdateView.as_view(), name="general"),
    path("changelog/", views.ChangelogListView.as_view(), name="changelog"),
    path(
        "personal/language/",
        views.PersonalLanguageUpdateView.as_view(),
        name="personal-language",
    ),
    path("personal/otp/", views.OTPView.as_view(), name="personal-otp"),
    path(
        "welcome_message/<slug:language>/<int:type>/",
        views.WelcomeMessageUpdateView.as_view(),
        name="welcome-message",
    ),
    path("integrations/", views.IntegrationsListView.as_view(), name="integrations"),
    path(
        "integrations/google_login",
        views.GoogleLoginSetupView.as_view(),
        name="google-login",
    ),
    path(
        "integrations/google_account",
        views.GoogleAccountCreationSetupView.as_view(),
        name="google-account",
    ),
    path(
        "integrations/slack_account",
        views.SlackAccountCreationSetupView.as_view(),
        name="slack-account",
    ),
    path("integrations/slack_bot", views.SlackBotSetupView.as_view(), name="slack-bot"),
    path(
        "integrations/<int:pk>",
        views.IntegrationDeleteView.as_view(),
        name="delete-integration",
    ),
    path("administrators/", views.AdministratorListView.as_view(), name="administrators"),
    path("administrators/<int:pk>/update/", views.AdministratorUpdateView.as_view(), name="administrators-update"),
    path(
        "administrators/create/",
        views.AdministratorCreateView.as_view(),
        name="administrators-create",
    ),
    path(
        "administrators/delete/<int:pk>/",
        views.AdministratorDeleteView.as_view(),
        name="administrators-delete",
    ),
]
