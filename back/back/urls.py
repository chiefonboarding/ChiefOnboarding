import sys

from django.conf import settings
from django.urls import include, path
from django.views.generic.base import TemplateView

from admin.admin_tasks import urls as admin_tasks_urls
from admin.appointments import urls as appointment_urls
from admin.badges import urls as badge_urls
from admin.integrations import urls as integrations_urls
from admin.introductions import urls as intro_urls
from admin.people import urls as people_urls
from admin.preboarding import urls as preboarding_urls
from admin.resources import urls as resource_urls
from admin.sequences import urls as sequences_urls
from admin.settings import urls as settings_urls
from admin.templates import urls as template_urls
from admin.to_do import urls as to_do_urls
from new_hire import urls as new_hire_urls
from organization import urls as org_urls
from slack_bot import urls as slack_urls
from user_auth import urls as auth_urls

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("", include(auth_urls)),
    path("api/org/", include(org_urls)),
    path("admin/people/", include((people_urls, "admin.people"), namespace="admin")),
    path("admin/settings/", include(settings_urls)),
    path("admin/tasks/", include(admin_tasks_urls)),
    # path("api/", include("rest_framework.urls")),
    # path("api/", include(note_urls)),
    path("templates/", include(template_urls)),
    path("templates/todo/", include(to_do_urls)),
    path("templates/introductions/", include(intro_urls)),
    path("templates/resources/", include(resource_urls)),
    path("templates/badges/", include(badge_urls)),
    # path("api/users/", include(user_urls)),
    path("new_hire/", include(new_hire_urls)),
    path("templates/preboarding/", include(preboarding_urls)),
    path("templates/appointments/", include(appointment_urls)),
    path("sequences/", include(sequences_urls)),
    path("api/slack/", include(slack_urls)),
    # path("api/integrations/", include(integrations_urls)),
]

# DJANGO DEBUG BAR
if settings.DEBUG and not 'pytest' in sys.modules:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
