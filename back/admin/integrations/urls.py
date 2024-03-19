from django.urls import path

from . import views
from . import builder_views

app_name = "integrations"
urlpatterns = [
    path("slack", views.SlackOAuthView.as_view(), name="slack"),
    path("create", views.IntegrationCreateView.as_view(), name="create"),
    path(
        "delete/<int:pk>/",
        views.IntegrationDeleteView.as_view(),
        name="delete",
    ),
    path("update/<int:pk>/", views.IntegrationUpdateView.as_view(), name="update"),
    path(
        "create/google_login/",
        views.IntegrationCreateGoogleLoginView.as_view(),
        name="create-google",
    ),
    path("oauth/<int:pk>/", views.IntegrationOauthRedirectView.as_view(), name="oauth"),
    path(
        "oauth/<int:pk>/callback/",
        views.IntegrationOauthCallbackView.as_view(),
        name="oauth-callback",
    ),
    path(
        "update_creds/<int:pk>/",
        views.IntegrationUpdateExtraArgsView.as_view(),
        name="update-creds",
    ),
    path(
        "update_creds/<int:pk>/delete/<slug:secret>/",
        views.IntegrationDeleteExtraArgsView.as_view(),
        name="delete-creds",
    ),
    path(
        "tracker/",
        views.IntegrationTrackerListView.as_view(),
        name="trackers",
    ),
    path(
        "tracker/<int:pk>/",
        views.IntegrationTrackerDetailView.as_view(),
        name="tracker",
    ),
    path(
        "builder/json/",
        views.IntegrationTestDownloadJSONView.as_view(),
        name="builder-json",
    ),
    path(
        "builder/test/",
        views.IntegrationTestView.as_view(),
        name="builder-test",
    ),

    # builder
    path(
        "builder/",
        builder_views.IntegrationBuilderCreateView.as_view(),
        name="builder",
    ),
    path(
        "builder/<int:pk>/",
        builder_views.IntegrationBuilderView.as_view(),
        name="builder",
    ),
    path(
        "<int:integration_id>/builder/form/",
        builder_views.IntegrationBuilderFormCreateView.as_view(),
        name="manifest-form-add",
    ),
    path(
        "<int:integration_id>/builder/form/<int:pk>/update/",
        builder_views.IntegrationBuilderFormUpdateView.as_view(),
        name="manifest-form-update",
    ),
    path(
        "<int:integration_id>/builder/form/<int:pk>/delete/",
        builder_views.IntegrationBuilderFormDeleteView.as_view(),
        name="manifest-form-delete",
    ),
    path(
        "<int:integration_id>/builder/revoke/",
        builder_views.IntegrationBuilderRevokeCreateView.as_view(),
        name="manifest-revoke-add",
    ),
    path(
        "<int:integration_id>/builder/revoke/<int:pk>/update/",
        builder_views.IntegrationBuilderRevokeUpdateView.as_view(),
        name="manifest-revoke-update",
    ),
    path(
        "<int:integration_id>/builder/revoke/<int:pk>/delete/",
        builder_views.IntegrationBuilderRevokeDeleteView.as_view(),
        name="manifest-revoke-delete",
    ),
    path(
        "<int:pk>/builder/headers/", # manifest pk
        builder_views.IntegrationBuilderHeadersUpdateView.as_view(),
        name="manifest-headers-update",
    ),
    path(
        "<int:pk>/builder/exists/", # ManifestExist pk
        builder_views.IntegrationBuilderExistsUpdateView.as_view(),
        name="manifest-exists-update",
    ),
    path(
        "<int:pk>/builder/manifest_exists_form/create/", # manifest pk
        builder_views.IntegrationBuilderInitialDataFormCreateView.as_view(),
        name="manifest-initial-data-create",
    ),
    path(
        "<int:pk>/builder/manifest_exists_form/<int:initial_data_form_id>/delete/", # manifest pk, initial_data_form.id
        builder_views.IntegrationBuilderInitialDataFormDeleteView.as_view(),
        name="manifest-initial-data-delete",
    ),
    path(
        "<int:pk>/builder/user_info_form/create/", # manifest pk
        builder_views.IntegrationBuilderUserInfoFormCreateView.as_view(),
        name="manifest-user-info-create",
    ),
    path(
        "<int:pk>/builder/user_info_form/<int:user_info_form_id>/delete/", # manifest pk, user_info_form.id
        builder_views.IntegrationBuilderUserInfoFormDeleteView.as_view(),
        name="manifest-user-info-delete",
    ),
    path(
        "<int:integration_id>/builder/execute/",
        builder_views.IntegrationBuilderExecuteCreateView.as_view(),
        name="manifest-execute-add",
    ),
    path(
        "<int:integration_id>/builder/execute/<int:pk>/update/",
        builder_views.IntegrationBuilderExecuteUpdateView.as_view(),
        name="manifest-execute-update",
    ),
    path(
        "<int:integration_id>/builder/execute/<int:pk>/delete/",
        builder_views.IntegrationBuilderExecuteDeleteView.as_view(),
        name="manifest-execute-delete",
    ),
]
