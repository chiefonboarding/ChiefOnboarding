from django.urls import path

from admin.hardware import views

app_name = "hardware"
urlpatterns = [
    path("", views.HardwareListView.as_view(), name="list"),
    path("create/", views.HardwareCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.HardwareUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.HardwareDeleteView.as_view(), name="delete"),
]
