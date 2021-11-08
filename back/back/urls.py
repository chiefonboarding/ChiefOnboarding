"""back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path, re_path
from django.views.generic import RedirectView

from admin.admin_tasks import urls as admin_tasks_urls
from admin.appointments import urls as appointment_urls
from admin.badges import urls as badge_urls
from admin.integrations import urls as integrations_urls
from admin.introductions import urls as intro_urls
from admin.notes import urls as note_urls
from admin.people import urls as people_urls
from admin.preboarding import urls as preboarding_urls
from admin.resources import urls as resource_urls
from admin.sequences import urls as sequences_urls
from admin.settings import urls as settings_urls
from admin.to_do import urls as to_do_urls
from new_hire import urls as new_hire_urls
from organization import urls as org_urls
from organization import views
from slack_bot import urls as slack_urls
from user_auth import urls as auth_urls
from users import urls as user_urls

urlpatterns = [
    # path('', views.home),
    path("admin/people", include((people_urls, "admin.people"), namespace="admin")),
    path("admin/settings/", include(settings_urls)),
    re_path(
        r"^_nuxt/(?P<path>.*)$",
        RedirectView.as_view(url="/static/js/_nuxt/%(path)s", permanent=True),
    ),
    path("sw.js", RedirectView.as_view(url="/static/js/_nuxt/sw.js", permanent=True)),
    path("api/", include("rest_framework.urls")),
    path("api/", include(note_urls)),
    path("templates/", include(to_do_urls)),
    path("api/", include(intro_urls)),
    path("api/", include(resource_urls)),
    path("api/", include(admin_tasks_urls)),
    path("api/", include(badge_urls)),
    path("api/users/", include(user_urls)),
    path("api/new_hire/", include(new_hire_urls)),
    path("api/", include(preboarding_urls)),
    path("api/", include(appointment_urls)),
    path("api/", include(sequences_urls)),
    path("api/slack/", include(slack_urls)),
    path("api/org/", include(org_urls)),
    path("", include(auth_urls)),
    path("api/integrations/", include(integrations_urls)),
]
