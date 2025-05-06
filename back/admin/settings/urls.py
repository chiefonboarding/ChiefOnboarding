from django.urls import path

from . import views
from . import email_template_views

app_name = "settings"
urlpatterns = [
    path("general/", views.OrganizationGeneralUpdateView.as_view(), name="general"),
    path("slack/", views.SlackSettingsUpdateView.as_view(), name="slack"),
    path("email/", views.EmailSettingsUpdateView.as_view(), name="email"),
    path("email/test/", views.TestEmailView.as_view(), name="email-test"),
    path("storage/", views.StorageSettingsUpdateView.as_view(), name="storage"),
    path("storage/migrate/", views.StorageMigrationView.as_view(), name="storage-migrate"),
    path("storage/migrate/local-to-s3/", views.StorageMigrateLocalToS3View.as_view(), name="storage-migrate-local-to-s3"),
    path("storage/migrate/s3-to-local/", views.StorageMigrateS3ToLocalView.as_view(), name="storage-migrate-s3-to-local"),
    path("ai-settings/", views.AISettingsUpdateView.as_view(), name="ai-settings"),
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
        "integrations/add_channel/",
        views.SlackChannelsCreateView.as_view(),
        name="slack-account-add-channel",
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
    # Email templates
    path(
        "email-templates/",
        email_template_views.EmailTemplateListView.as_view(),
        name="email-templates",
    ),
    path(
        "email-templates/create/",
        email_template_views.EmailTemplateCreateView.as_view(),
        name="email-templates-create",
    ),
    path(
        "email-templates/<int:pk>/update/",
        email_template_views.EmailTemplateUpdateView.as_view(),
        name="email-templates-update",
    ),
    path(
        "email-templates/<int:pk>/delete/",
        email_template_views.EmailTemplateDeleteView.as_view(),
        name="email-templates-delete",
    ),
    path(
        "email-templates/preview/",
        email_template_views.preview_email_template,
        name="email-templates-preview",
    ),
]
