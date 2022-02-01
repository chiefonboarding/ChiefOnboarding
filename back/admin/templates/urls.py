from django.urls import path

from . import views

app_name = "templates"
urlpatterns = [
    path(
        "duplicate/<slug:template_type>/<int:template_pk>/",
        views.TemplateDuplicateView.as_view(),
        name="duplicate",
    ),
]
