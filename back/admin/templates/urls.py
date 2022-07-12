from django.urls import path

from . import views

app_name = "templates"
urlpatterns = [
    path(
        "duplicate/<slug:template_type>/<int:template_pk>/",
        views.TemplateDuplicateView.as_view(),
        name="duplicate",
    ),
    path(
        "duplicate_seq/<int:template_pk>/",
        views.SequenceDuplicateView.as_view(),
        name="duplicate_seq",
    ),
]
