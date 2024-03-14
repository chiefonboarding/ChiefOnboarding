from django.urls import path

from . import views

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
        views.IntegrationBuilderCreateView.as_view(),
        name="builder",
    ),
    path(
        "builder/<int:pk>/",
        views.IntegrationBuilderView.as_view(),
        name="builder",
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
        "<int:integration_id>/builder/form/",
        views.IntegrationBuilderFormCreateView.as_view(),
        name="manifest-form-add",
    ),
]
