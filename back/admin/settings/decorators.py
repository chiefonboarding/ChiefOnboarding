from functools import wraps

from django.conf import settings
from django.http import Http404


def requires_credentials_login(view_func):
    @wraps(view_func)
    def _wrapper_view(request, *args, **kwargs):
        if settings.SOCIALACCOUNT_ONLY:
            raise Http404
        return view_func(request, *args, **kwargs)

    return _wrapper_view
