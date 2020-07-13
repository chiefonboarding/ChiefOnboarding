from django.utils import translation


def language_middleware(get_response):
    def middleware(request):
        # Set user's language
        if request.user.is_authenticated:
            translation.activate(request.user.language)
        # Code to be executed for each request/response after
        # the view is called.
        response = get_response(request)
        return response

    return middleware
