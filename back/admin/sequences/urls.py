from django.urls import include, path

from . import views

app_name = "sequences"
urlpatterns = [
    path("", views.SequenceListView.as_view(), name="list"),
    path("create/", views.SequenceCreateView.as_view(), name="create"),
    path("<int:pk>/", views.SequenceView.as_view(), name="update"),
    path("<int:pk>/delete/", views.SequenceDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/timeline/",
        views.SequenceTimelineDetailView.as_view(),
        name="timeline",
    ),
    path(
        "<int:pk>/update_name/",
        views.SequenceNameUpdateView.as_view(),
        name="update_name",
    ),
    path(
        "<int:pk>/condition/",
        views.SequenceConditionCreateView.as_view(),
        name="condition-create",
    ),
    path(
        "<int:sequence_pk>/condition/<int:pk>/",
        views.SequenceConditionUpdateView.as_view(),
        name="condition-update",
    ),
    path(
        "condition/<int:pk>/to_do/",
        views.SequenceConditionToDoUpdateView.as_view(),
        name="condition-to-do-update",
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
        "update_item/<slug:template_type>/<int:template_pk>/<int:condition>/",
        views.SequenceFormUpdateView.as_view(),
        name="update-forms",
    ),
    path("templates/", views.SequenceDefaultTemplatesView.as_view(), name="template_list"),
    # path("external_messages", views.SaveExternalMessage.as_view()),
    # path("send_test_message/<int:id>/", views.SendTestMessage.as_view()),
    # path("sequence/admin_task/", views.SaveAdminTask.as_view()),
]
