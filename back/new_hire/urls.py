from django.urls import include, path
from rest_framework import routers

from new_hire import views

router = routers.DefaultRouter(trailing_slash=False)
# router.register('notes', views.NoteViewSet, 'notes')

app_name = "new_hire"
urlpatterns = [
    path("", include(router.urls)),
    path("authenticate", views.AuthenticateView.as_view()),
    path("me", views.MeView.as_view()),
    path("to_do", views.ToDoView.as_view()),
    path("to_do/<int:id>", views.ToDoView.as_view()),
    path("to_do_preboarding/<int:id>", views.ToDoPreboardingView.as_view()),
    path("slack/to_do/<int:id>", views.ToDoSlackView.as_view()),
    path("colleagues", views.ColleagueView.as_view()),
    path("introductions", views.IntroductionView.as_view()),
    # path("preboarding", views.PreboardingView.as_view()),
    path("resources", views.ResourceView.as_view()),
    path("badges", views.BadgeView.as_view()),
    path("resource/<int:id>", views.ResourceItemView.as_view()),
    path("change_step/<int:id>", views.CourseStep.as_view()),
    path("course/<int:id>", views.CourseItemView.as_view()),
    # native views
    path("todos/", views.NewHireDashboard.as_view(), name="todos"),
    path("todos/<int:pk>/", views.ToDoDetailView.as_view(), name="to_do"),
    path("todos/<int:pk>/complete/", views.ToDoCompleteView.as_view(), name="to_do_complete"),
    path("colleagues/", views.ColleagueListView.as_view(), name="colleagues"),
    path("preboarding/", views.PreboardingShortURLRedirectView.as_view(), name="preboarding-url"),
    path("preboarding/<int:pk>/", views.PreboardingDetailView.as_view(), name="preboarding"),
]
