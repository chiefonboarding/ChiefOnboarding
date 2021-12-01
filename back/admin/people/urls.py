from django.urls import path

from . import views

app_name = "people"
urlpatterns = [
    path("/", views.NewHireListView.as_view(), name="new_hires"),
    path("/new_hire/add/", views.NewHireAddView.as_view(), name="new_hire_add"),
    path("/new_hire/<int:pk>/overview/", views.NewHireSequenceView.as_view(), name="new_hire"),
    path("/new_hire/<int:pk>/profile/", views.NewHireProfileView.as_view(), name="new_hire_profile"),
    path("/new_hire/<int:pk>/notes/", views.NewHireNotesView.as_view(), name="new_hire_notes"),
    path(
        "/new_hire/<int:pk>/welcome_messages/",
        views.NewHireWelcomeMessagesView.as_view(),
        name="new_hire_welcome_messages",
    ),
    path("/new_hire/<int:pk>/admin_tasks/", views.NewHireAdminTasksView.as_view(), name="new_hire_admin_tasks"),
    path("/new_hire/<int:pk>/forms/", views.NewHireFormsView.as_view(), name="new_hire_forms"),
    path("/new_hire/<int:pk>/progress/", views.NewHireProgressView.as_view(), name="new_hire_progress"),
    path("/new_hire/<int:pk>/tasks/", views.NewHireTasksView.as_view(), name="new_hire_tasks"),
    path("/colleagues/", views.ColleagueListView.as_view(), name="colleagues"),
    path("/colleagues/<int:pk>/", views.ColleagueUpdateView.as_view(), name="colleague"),
    path("/colleagues/<int:pk>/delete", views.ColleagueDeleteView.as_view(), name="colleague_delete"),
]
