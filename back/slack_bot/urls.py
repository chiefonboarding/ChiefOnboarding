from django.urls import path
from django.conf import settings
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def slack_events_handler(request: HttpRequest):
    return handler.handle(request)


app_name = "slack"
if not settings.SLACK_USE_SOCKET:
    from .views import app

    from slack_bolt.adapter.django import SlackRequestHandler

    handler = SlackRequestHandler(app=app)
    urlpatterns = [
        path("slack/events", slack_events_handler, name="slack_events"),
    ]
else:
    urlpatterns = []
