from django.urls import path

from admin.sequences import offboarding_views, views

app_name = "sequences"
urlpatterns = [
    path("", views.SequenceListView.as_view(), name="list"),
    path("create/", views.SequenceCreateView.as_view(), name="create"),
    path("<int:pk>/", views.SequenceView.as_view(), name="update"),
    path("<int:pk>/delete/", views.SequenceDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/update_name/",
        views.SequenceNameUpdateView.as_view(),
        name="update_name",
    ),
    path(
        "<int:sequence_pk>/condition/",
        views.SequenceConditionCreateView.as_view(),
        name="condition-create",
    ),
    path(
        "<int:sequence_pk>/condition/<int:pk>/",
        views.SequenceConditionUpdateView.as_view(),
        name="condition-update",
    ),
    path(
        "<int:pk>/condition/<int:condition_pk>/delete/",
        views.SequenceConditionDeleteView.as_view(),
        name="condition-delete",
    ),
    path(
        "condition/<int:pk>/<slug:type>/<int:template_pk>/",
        views.SequenceConditionItemView.as_view(),
        name="template_condition",
    ),
    path(
        "forms/<slug:template_type>/<int:template_pk>/",
        views.SequenceFormView.as_view(),
        name="forms",
    ),
    path(
        "send_test_message/<int:template_pk>/",
        views.SendTestMessageView.as_view(),
        name="send_test_message",
    ),
    path(
        "update_item/<slug:template_type>/<int:template_pk>/<int:condition>/",
        views.SequenceFormUpdateView.as_view(),
        name="update-forms",
    ),
    path(
        "update_integration_config/<slug:template_type>/<int:template_pk>/<int:condition>/<int:exists>/",  # noqa: E501
        views.SequenceFormUpdateIntegrationConfigView.as_view(),
        name="update-integration-config",
    ),
    path(
        "<int:pk>/templates/",
        views.SequenceDefaultTemplatesView.as_view(),
        name="template_list",
    ),
    # offboarding urls
    path(
        "offboarding",
        offboarding_views.OffboardingSequenceListView.as_view(),
        name="offboarding-list",
    ),
    path(
        "offboarding/create/",
        views.SequenceCreateView.as_view(),
        name="offboarding-create",
    ),
]
