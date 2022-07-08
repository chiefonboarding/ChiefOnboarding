import logging

from django.conf import settings
from django.http import HttpRequest
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
def slack_events_handler(request: HttpRequest):
    return handler.handle(request)


app_name = "slack"
urlpatterns = []

if not settings.SLACK_USE_SOCKET:
    from slack_bolt.adapter.django import SlackRequestHandler

    try:
        from .views import app

        handler = SlackRequestHandler(app=app)
        urlpatterns = [
            path("bot", slack_events_handler, name="slack_events"),
        ]
    except Exception as e:
        logger.error("Couldn't start slack app: " + str(e))

elif settings.SLACK_APP_TOKEN != "":
    # Start websocket app
    from .views import app
