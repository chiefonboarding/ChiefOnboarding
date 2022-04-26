from django.urls import path

from . import views

app_name = "slack"
urlpatterns = [
    path("bot", views.BotView.as_view(), name="bot"),
    path("callback", views.CallbackView.as_view(), name="callback"),
]
