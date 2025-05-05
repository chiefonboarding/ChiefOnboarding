from django.urls import path

from . import views
from . import ai_views
from . import pdf_views

app_name = "api"
urlpatterns = [
    path("users/", views.UserView.as_view(), name="users"),
    path("employees/", views.EmployeeView.as_view(), name="employees"),
    path("sequences/", views.SequenceView.as_view(), name="sequences"),
    path("ai-content-generate/", ai_views.generate_ai_content, name="ai-content-generate"),
    path("pdf-extract-questions/", pdf_views.extract_questions_from_pdf, name="pdf-extract-questions"),
]
