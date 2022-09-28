from django.urls import path

from . import views

app_name = "settings"
urlpatterns = [
    path("general/", views.OrganizationGeneralUpdateView.as_view(), name="general"),
    path("slack/", views.SlackSettingsUpdateView.as_view(), name="slack"),
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
    path(
        "welcome_message/<slug:language>/<int:type>/test_message/",
        views.WelcomeMessageSendTestMessageView.as_view(),
        name="welcome-message-test-message",
    ),
    path("integrations/", views.IntegrationsListView.as_view(), name="integrations"),
    path(
        "integrations/slack_account/update_channels/",
        views.SlackChannelsUpdateView.as_view(),
        name="slack-account-update-channels",
    ),
    path(
        "integrations/slack_bot/", views.SlackBotSetupView.as_view(), name="slack-bot"
    ),
    path(
        "administrators/", views.AdministratorListView.as_view(), name="administrators"
    ),
    path(
        "administrators/<int:pk>/update/",
        views.AdministratorUpdateView.as_view(),
        name="administrators-update",
    ),
    path(
        "administrators/create/",
        views.AdministratorCreateView.as_view(),
        name="administrators-create",
    ),
    path(
        "administrators/<int:pk>/delete/",
        views.AdministratorDeleteView.as_view(),
        name="administrators-delete",
    ),
]
