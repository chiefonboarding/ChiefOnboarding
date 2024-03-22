from django.urls import path

from . import builder_views, views

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
        "builder/",
        builder_views.IntegrationBuilderCreateView.as_view(),
        name="builder",
    ),
    path(
        "builder/<int:pk>/",
        builder_views.IntegrationBuilderView.as_view(),
        name="builder-detail",
    ),
    path(
        "<int:pk>/builder/form/",
        builder_views.IntegrationBuilderFormCreateView.as_view(),
        name="manifest-form-add",
    ),
    path(
        "<int:pk>/builder/form/<int:index>/update/",
        builder_views.IntegrationBuilderFormUpdateView.as_view(),
        name="manifest-form-update",
    ),
    path(
        "<int:pk>/builder/form/<int:index>/delete/",
        builder_views.IntegrationBuilderFormDeleteView.as_view(),
        name="manifest-form-delete",
    ),
    path(
        "<int:pk>/builder/revoke/",
        builder_views.IntegrationBuilderRevokeCreateView.as_view(),
        name="manifest-revoke-add",
    ),
    path(
        "<int:pk>/builder/revoke/<int:index>/update/",
        builder_views.IntegrationBuilderRevokeUpdateView.as_view(),
        name="manifest-revoke-update",
    ),
    path(
        "<int:pk>/builder/revoke/<int:index>/delete/",
        builder_views.IntegrationBuilderRevokeDeleteView.as_view(),
        name="manifest-revoke-delete",
    ),
    path(
        "<int:pk>/builder/headers/",  # manifest pk
        builder_views.IntegrationBuilderHeadersUpdateView.as_view(),
        name="manifest-headers-update",
    ),
    path(
        "<int:pk>/builder/exists/",  # ManifestExist pk
        builder_views.IntegrationBuilderExistsUpdateView.as_view(),
        name="manifest-exists-update",
    ),
    path(
        "<int:pk>/builder/manifest_exists_form/create/",  # manifest pk
        builder_views.IntegrationBuilderInitialDataFormCreateView.as_view(),
        name="manifest-initial-data-create",
    ),
    path(
        "<int:pk>/builder/manifest_exists_form/<int:index>/delete/",  # manifest pk, initial_data_form.id
        builder_views.IntegrationBuilderInitialDataFormDeleteView.as_view(),
        name="manifest-initial-data-delete",
    ),
    path(
        "<int:pk>/builder/user_info_form/create/",  # manifest pk
        builder_views.IntegrationBuilderUserInfoFormCreateView.as_view(),
        name="manifest-user-info-create",
    ),
    path(
        "<int:pk>/builder/user_info_form/<int:index>/delete/",  # manifest pk, user_info_form.id
        builder_views.IntegrationBuilderUserInfoFormDeleteView.as_view(),
        name="manifest-user-info-delete",
    ),
    path(
        "<int:pk>/builder/execute/",
        builder_views.IntegrationBuilderExecuteCreateView.as_view(),
        name="manifest-execute-add",
    ),
    path(
        "<int:pk>/builder/execute/<int:index>/update/",
        builder_views.IntegrationBuilderExecuteUpdateView.as_view(),
        name="manifest-execute-update",
    ),
    path(
        "<int:pk>/builder/execute/<int:index>/delete/",
        builder_views.IntegrationBuilderExecuteDeleteView.as_view(),
        name="manifest-execute-delete",
    ),
    path(
        "<int:pk>/builder/test_form/",
        builder_views.IntegrationBuilderTestFormView.as_view(),
        name="manifest-test-form",
    ),
    path(
        "<int:pk>/builder/test_exists/",
        builder_views.IntegrationBuilderTestExistsView.as_view(),
        name="manifest-test-exists",
    ),
]
