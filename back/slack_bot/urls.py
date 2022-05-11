from django.conf import settings
from django.http import HttpRequest
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import app


@csrf_exempt
def slack_events_handler(request: HttpRequest):
    return handler.handle(request)


app_name = "slack"
if not settings.SLACK_USE_SOCKET:
    from slack_bolt.adapter.django import SlackRequestHandler

    handler = SlackRequestHandler(app=app)
    urlpatterns = [
        path("slack/events", slack_events_handler, name="slack_events"),
    ]
else:
    urlpatterns = []
