from django.conf import settings
from django.urls import include, path

from . import views

if settings.ALLOW_LOGIN_WITH_CREDENTIALS:
    from allauth.mfa.recovery_codes.views import download_recovery_codes
else:

    def download_recovery_codes():
        pass


app_name = "settings"
urlpatterns = [
    path("general/", views.OrganizationGeneralUpdateView.as_view(), name="general"),
    path("slack/", views.SlackSettingsUpdateView.as_view(), name="slack"),
    path(
        "personal/language/",
        views.PersonalLanguageUpdateView.as_view(),
        name="personal-language",
    ),
    path(
        "personal/2fa/",
        include(
            [
                path("", views.TOTPIndexView.as_view(), name="totp"),
                path(
                    "totp/",
                    include(
                        [
                            path(
                                "activate/",
                                views.TOTPActivateView.as_view(),
                                name="mfa_activate_totp",
                            ),
                            path(
                                "deactivate/",
                                views.TOTPDeactivateView.as_view(),
                                name="mfa_deactivate_totp",
                            ),
                        ]
                    ),
                ),
                path(
                    "recovery-codes/",
                    include(
                        [
                            path(
                                "generate/",
                                views.TOTPGenerateRecoveryCodesView.as_view(),
                                name="mfa_generate_recovery_codes",
                            ),
                            path(
                                "download/",
                                download_recovery_codes,
                                name="mfa_download_recovery_codes",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
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
]
