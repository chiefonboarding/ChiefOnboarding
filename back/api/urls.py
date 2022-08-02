from django.urls import path

from . import views

app_name = "api"
urlpatterns = [
    path("newhires/", views.UserView.as_view(), name="newhires"),
    path("employees/", views.EmployeeView.as_view(), name="employees"),
    path("sequences/", views.SequenceView.as_view(), name="sequences"),
]
