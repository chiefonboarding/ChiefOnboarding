from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path('bot', views.BotView.as_view()),
    path('callback', views.CallbackView.as_view()),
    path('channels', views.SlackChannelsView.as_view())
]