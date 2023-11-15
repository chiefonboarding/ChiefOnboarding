import os
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from misc.models import File
from misc.s3 import S3
from misc.serializers import FileSerializer
from slack_bot.models import SlackChannel
from users.mixins import AdminPermMixin, LoginRequiredMixin, ManagerPermMixin
from users.models import User

from .forms import InitalAdminAccountForm
from .models import Notification, Organization


class FileView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = [
        SessionAuthentication,
    ]

    def get(self, request, id, uuid):
        file = get_object_or_404(File, uuid=uuid, id=id)
        url = file.get_url()
        return Response(url)

    def post(self, request):
        ext = ""
        if len(request.data["name"].split(".")) > 1:
            ext = request.data["name"].split(".")[-1]

        serializer = FileSerializer(
            data={
                "name": request.data["name"],
                "ext": ext,
            }
        )
        serializer.is_valid(raise_exception=True)
        f = serializer.save()
        key = (
            f"{f.id}-{serializer.data['name'].split('.')[0]}/{serializer.data['name']}"
        )
        f.key = key
        f.save()
        # Specifics based on Editor.js expectations
        return Response(
            {
                "success": 1,
                "file": {
                    "url": S3().get_presigned_url(key),
                    "id": f.id,
                    "name": f.name,
                    "ext": f.ext,
                    "get_url": f.get_url(),
                    "size": None,
                    "title": f.name,
                },
            }
        )

    def delete(self, request, id):
        if request.user.is_admin_or_manager:
            file = get_object_or_404(File, pk=id)
            file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "notifications.html"
    queryset = Notification.objects.all().select_related("created_by", "created_for")
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Notifications")
        context["subtitle"] = _("global")
        return context


class InitialSetupView(CreateView):
    template_name = "initial_setup.html"
    form_class = InitalAdminAccountForm

    def dispatch(self, *args, **kwargs):
        # Make sure organization doesn't exist yet
        if Organization.objects.all().exists():
            raise Http404
        return super().dispatch(*args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        org = Organization.objects.create(
            name=form.cleaned_data["name"],
            timezone=form.cleaned_data["timezone"],
            language=form.cleaned_data["language"],
            slack_default_channel=SlackChannel.objects.get(name="general"),
        )
        admin_user = get_user_model().objects.create(
            # TODO: switch to script with factory boy instead of json files
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            email=form.cleaned_data["email"],
            language=org.language,
            timezone=org.timezone,
            role=get_user_model().Role.ADMIN,
        )
        admin_user.set_password(raw_password=form.cleaned_data["password1"])
        admin_user.save()

        welcome_message_path = os.path.join(
            settings.BASE_DIR, "fixtures/welcome_message.json"
        )
        all_path = os.path.join(settings.BASE_DIR, "fixtures/all.json")
        management.call_command("loaddata", welcome_message_path, verbosity=0)
        management.call_command("loaddata", all_path, verbosity=0)

        # Rotate start date, unique url, and password from fixture
        demo_user = User.objects.get(email="john@chiefonboarding.com")
        demo_user.set_unusable_password()
        demo_user.unique_url = get_random_string(length=8)
        demo_user.start_day = timezone.now().date() + timedelta(days=5)
        demo_user.save()

        return redirect("login")


class SearchHXView(LoginRequiredMixin, ManagerPermMixin, TemplateView):
    template_name = "search_results.html"

    def _get_relevant_items_from_model(self, lookup_model, query):
        model = apps.get_model(lookup_model["app"], lookup_model["model"])
        if lookup_model["model"] == "User":
            objects = model.objects.filter(
                Q(first_name__search=query) | Q(last_name__search=query)
            )
        elif lookup_model.get("templates", False):
            objects = model.templates.filter(name__search=query)
        else:
            objects = model.objects.filter(name__search=query)

        return [
            {"name": obj.name, "url": obj.update_url, "icon": obj.get_icon_template}
            for obj in objects
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        lookup_models = [
            {"app": "to_do", "model": "ToDo", "templates": True},
            {"app": "resources", "model": "Resource", "templates": True},
            {"app": "badges", "model": "Badge", "templates": True},
            {"app": "appointments", "model": "Appointment", "templates": True},
            {"app": "introductions", "model": "Introduction", "templates": True},
            {"app": "preboarding", "model": "Preboarding", "templates": True},
            {"app": "integrations", "model": "Integration"},
            {"app": "sequences", "model": "Sequence"},
            {"app": "hardware", "model": "Hardware", "template": True},
            {"app": "users", "model": "User"},
        ]
        results = []
        for item in lookup_models:
            results += self._get_relevant_items_from_model(item, query)
        context["results"] = results[:20]
        context["more_results"] = len(results) > 20
        return context
