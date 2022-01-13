from django.urls import include, path

from . import views

app_name = "sequences"
urlpatterns = [
    path("sequences/", views.SequenceListView.as_view(), name="list"),
    path("sequences/create/", views.SequenceCreateView.as_view(), name="create"),
    path("sequences/<int:pk>/", views.SequenceView.as_view(), name="update"),
    path("sequences/<int:pk>/delete/", views.SequenceDeleteView.as_view(), name="delete"),
    path("sequences/<int:pk>/timeline/", views.SequenceTimelineDetailView.as_view(), name="timeline"),
    path("sequences/<int:pk>/update_name/", views.SequenceNameUpdateView.as_view(), name="update_name"),
    path("sequences/<int:pk>/condition/", views.SequenceConditionCreateView.as_view(), name="condition-create"),
    path("sequences/condition/<int:pk>/to_do/", views.SequenceConditionToDoUpdateView.as_view(), name="condition-to-do-update"),
    path("sequences/<int:pk>/condition/<int:condition_pk>/delete/", views.SequenceConditionDeleteView.as_view(), name="condition-delete"),
    path("sequences/condition/<int:pk>/<slug:type>/<int:template_pk>/", views.SequenceConditionItemView.as_view(), name="template_condition"),
    path("sequences/templates/", views.SequenceDefaultTemplatesView.as_view(), name="template_list"),
    # path("external_messages", views.SaveExternalMessage.as_view()),
    # path("send_test_message/<int:id>/", views.SendTestMessage.as_view()),
    # path("sequence/admin_task/", views.SaveAdminTask.as_view()),
]
