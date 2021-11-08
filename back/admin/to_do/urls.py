from django.urls import include, path
from rest_framework import routers

from admin.to_do import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("to_do", views.ToDoViewSet, "to_do")

app_name = 'todo'
urlpatterns = [
    path("", include(router.urls)),
    path('todo/', views.ToDoListView.as_view(), name="list"),
    path('todo/create', views.ToDoCreateView.as_view(), name="create"),
    path('todo/<int:pk>/edit', views.ToDoUpdateView.as_view(), name="update"),
]
