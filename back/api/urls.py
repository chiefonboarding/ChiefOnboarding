from django.urls import path

from . import views

app_name = "api"
urlpatterns = [
    path("users/", views.UserView.as_view(), name="users"),
    path("offboarding/", views.UserOffboardingView.as_view(), name="offboarding"),
    path("employees/", views.EmployeeView.as_view(), name="employees"),
    path("sequences/", views.SequenceView.as_view(), name="sequences"),
]
