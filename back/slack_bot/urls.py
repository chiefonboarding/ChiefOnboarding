from django.conf import settings
from django.http import HttpRequest
from django.urls import path
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def slack_events_handler(request: HttpRequest):
    return handler.handle(request)


app_name = "slack"
if not settings.SLACK_USE_SOCKET:
    from slack_bolt.adapter.django import SlackRequestHandler

    from .views import app

    handler = SlackRequestHandler(app=app)
    urlpatterns = [
        path("bot/", slack_events_handler, name="slack_events"),
    ]
elif settings.SLACK_APP_TOKEN != "":
    # Start websocket app
    from .views import app

    urlpatterns = []
else:
    urlpatterns = []
