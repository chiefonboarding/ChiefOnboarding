from django.urls import path

from . import views

urlpatterns = [
    path("/", views.NewHireListView.as_view(), name="new_hires"),
]
