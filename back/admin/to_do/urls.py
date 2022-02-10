from django.urls import path

from admin.to_do import views

app_name = "todo"
urlpatterns = [
    path("", views.ToDoListView.as_view(), name="list"),
    path("create", views.ToDoCreateView.as_view(), name="create"),
    path("<int:pk>/edit", views.ToDoUpdateView.as_view(), name="update"),
    path("<int:pk>/delete", views.ToDoDeleteView.as_view(), name="delete"),
]
