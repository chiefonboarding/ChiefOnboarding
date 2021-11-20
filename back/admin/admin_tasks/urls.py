from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("admin_tasks", views.AdminTaskViewSet, "admin_tasks")

app_name = "admin_tasks"
urlpatterns = [
    path("", include(router.urls)),
    path("/mine/", views.MyAdminTasksListView.as_view(), name="mine"),
    path("/all/", views.AllAdminTasksListView.as_view(), name="all"),
    path("/<int:pk>/", views.AdminTasksUpdateView.as_view(), name="detail"),
    path("/<int:pk>/comment/", views.AdminTasksCommentCreateView.as_view(), name="comment"),
]


