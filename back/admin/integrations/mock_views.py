"""Fake third party endpoint used to test integrations without hitting real APIs.

Only routed when ``settings.TEST_INTEGRATIONS_ENDPOINT`` is True. Point an
integration's URL at ``{BASE_URL}/test-integrations/`` (subpaths are not
supported) and control the response through query params:

    status        HTTP status code to return (100-599, default 200)
    delay         seconds to wait before responding (float, max 10, default 0)
    body          raw response body (default ``{}``)
    content_type  response Content-Type (default ``application/json``)
    echo          if truthy, respond with a JSON dump of the incoming request
                  (method, query params and body) instead of ``body``; useful to
                  check what an integration sent

Example:
    /test-integrations/?status=201&delay=1.5&body={"id":"abc"}
"""

import json
import time

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

MAX_DELAY_SECONDS = 10
TRUTHY = {"1", "true", "yes", "on"}


@method_decorator([csrf_exempt, login_not_required], name="dispatch")
class MockIntegrationView(View):
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def dispatch(self, request, *args, **kwargs):
        # Second guard in case the URL ever gets routed without the flag.
        if not settings.TEST_INTEGRATIONS_ENDPOINT:
            raise Http404

        if request.method.lower() not in self.http_method_names:
            return self.http_method_not_allowed(request, *args, **kwargs)
        return self.mock_response(request)

    def mock_response(self, request):
        params = request.GET

        try:
            status = int(params.get("status", 200))
            delay = float(params.get("delay", 0))
        except ValueError:
            return HttpResponseBadRequest("'status' and 'delay' must be numbers")
        if not 100 <= status <= 599:
            return HttpResponseBadRequest("'status' must be between 100 and 599")
        if not 0 <= delay <= MAX_DELAY_SECONDS:
            return HttpResponseBadRequest(
                f"'delay' must be between 0 and {MAX_DELAY_SECONDS}"
            )

        if params.get("echo", "").lower() in TRUTHY:
            content_type = "application/json"
            body = json.dumps(
                {
                    "method": request.method,
                    "query": {key: params.getlist(key) for key in params},
                    "body": request.body.decode("utf-8", errors="replace"),
                }
            )
        else:
            content_type = params.get("content_type", "application/json")
            body = params.get("body", "{}")

        if delay:
            time.sleep(delay)

        return HttpResponse(body, status=status, content_type=content_type)
