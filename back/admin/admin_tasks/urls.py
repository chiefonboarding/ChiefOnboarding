from django.urls import path

from . import views

app_name = "admin_tasks"
urlpatterns = [
    path("create/", views.AdminTasksCreateView.as_view(), name="create"),
    path("mine/", views.MyAdminTasksListView.as_view(), name="mine"),
    path("all/", views.AllAdminTasksListView.as_view(), name="all"),
    path("<int:pk>/", views.AdminTasksUpdateView.as_view(), name="detail"),
    path("<int:pk>/completed/", views.AdminTaskToggleDoneView.as_view(), name="completed"),
    path("<int:pk>/comment/", views.AdminTasksCommentCreateView.as_view(), name="comment"),
]
