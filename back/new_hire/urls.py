from django.urls import path

from new_hire import views

app_name = "new_hire"
urlpatterns = [
    path("todos/", views.NewHireDashboard.as_view(), name="todos"),
    path("resources/", views.ResourceListView.as_view(), name="resources"),
    path(
        "resources/<int:pk>/<int:chapter>/",
        views.ResourceDetailView.as_view(),
        name="resource-detail",
    ),
    path(
        "form/<int:pk>/<int:chapter>/",
        views.CourseAnswerView.as_view(),
        name="question-form",
    ),
    path(
        "course/<int:pk>/", views.CourseNextStepView.as_view(), name="course-next-step"
    ),
    path("todos/<int:pk>/", views.ToDoDetailView.as_view(), name="to_do"),
    path(
        "todos/<int:pk>/complete/",
        views.ToDoCompleteView.as_view(),
        name="to_do_complete",
    ),
    path("colleagues/", views.ColleagueListView.as_view(), name="colleagues"),
    path(
        "colleagues/search/",
        views.ColleagueSearchView.as_view(),
        name="colleagues-search",
    ),
    path(
        "preboarding/",
        views.PreboardingShortURLRedirectView.as_view(),
        name="preboarding-url",
    ),
    path(
        "preboarding/<int:pk>/",
        views.PreboardingDetailView.as_view(),
        name="preboarding",
    ),
]
