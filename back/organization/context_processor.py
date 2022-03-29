from .models import Organization


def org_include(request):
    try:
        return {
            "org": Organization.objects.first(),
        }
    except Exception:
        # will only fail when user has not ran migrations yet. Org is set up during
        # first migrations
        return {"org": Organization.objects.none()}
