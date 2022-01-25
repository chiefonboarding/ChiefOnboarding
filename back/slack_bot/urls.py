from django.urls import path

from . import views

urlpatterns = [
    path("bot", views.BotView.as_view()),
    path("callback", views.CallbackView.as_view()),
]
