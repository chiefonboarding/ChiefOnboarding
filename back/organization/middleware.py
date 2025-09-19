from django.http import HttpResponse
from django.shortcuts import redirect

from organization.models import Organization


# Credits: https://stackoverflow.com/a/64623669
class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health":
            return HttpResponse("ok")
        return self.get_response(request)


class SetupOrgMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org = Organization.object.get()
        if org is None and request.path != "/setup/":
            return redirect("setup")
        return self.get_response(request)
