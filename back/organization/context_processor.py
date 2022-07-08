from django.conf import settings

from .models import Organization


def org_include(request):
    try:
        return {
            "org": Organization.objects.first(),
            "DEBUG": settings.DEBUG,
        }
    except Exception:
        # will only fail when user has not ran migrations yet. Org is set up during
        # first migrations
        return {"org": Organization.objects.none(), "DEBUG": settings.DEBUG}
