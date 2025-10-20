from django.urls import path

from . import views

app_name = "ai_assistant"
urlpatterns = [
    path("", views.AIAssistantView.as_view(), name="index"),
    path("chat/", views.AIAssistantChatView.as_view(), name="chat"),
    path("reset/", views.AIAssistantResetView.as_view(), name="reset"),
]
