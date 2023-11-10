from django.conf import settings
from django.urls import include, path
from django.views.generic.base import TemplateView

import user_auth
from admin.admin_tasks import urls as admin_tasks_urls
from admin.appointments import urls as appointment_urls
from admin.badges import urls as badge_urls
from admin.hardware import urls as hardware_urls
from admin.integrations import urls as integrations_urls
from admin.introductions import urls as intro_urls
from admin.people import urls as people_urls
from admin.preboarding import urls as preboarding_urls
from admin.resources import urls as resource_urls
from admin.sequences import urls as sequences_urls
from admin.settings import urls as settings_urls
from admin.templates import urls as template_urls
from admin.to_do import urls as to_do_urls
from api import urls as public_api_urls
from new_hire import urls as new_hire_urls
from organization import urls as org_urls
from organization import views as org_views
from slack_bot import urls as slack_urls
from user_auth import urls as auth_urls

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("", include(auth_urls)),
    path(
        "api/auth/google_login",
        user_auth.views.GoogleLoginView.as_view(),
        name="google_login",
    ),
    path("api/org/", include(org_urls)),
    path("setup/", org_views.InitialSetupView.as_view(), name="setup"),
    path("admin/people/", include((people_urls, "admin.people"), namespace="admin")),
    path("admin/settings/", include(settings_urls)),
    path("admin/tasks/", include(admin_tasks_urls)),
    path("admin/templates/", include(template_urls)),
    path("admin/templates/todo/", include(to_do_urls)),
    path("admin/templates/hardware/", include(hardware_urls)),
    path("admin/templates/introductions/", include(intro_urls)),
    path("admin/templates/resources/", include(resource_urls)),
    path("admin/templates/badges/", include(badge_urls)),
    path("admin/templates/preboarding/", include(preboarding_urls)),
    path("admin/templates/appointments/", include(appointment_urls)),
    path("new_hire/", include(new_hire_urls)),
    path("admin/sequences/", include(sequences_urls)),
    path("api/slack/", include(slack_urls)),
    path("admin/integrations/", include(integrations_urls)),
]

# API
if settings.API_ACCESS:
    urlpatterns += [
        path("api/", include(public_api_urls)),
    ]

# DJANGO DEBUG BAR
if settings.DEBUG and not settings.RUNNING_TESTS:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
