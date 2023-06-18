from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from django.conf import settings

from admin.integrations.models import Integration
from admin.resources.models import Resource
from organization.models import WelcomeMessage
from slack_bot.utils import Slack, actions, button, paragraph
from users.emails import email_new_admin_cred
from users.mixins import (
    IsAdminOrNewHireManagerMixin,
    LoginRequiredMixin,
    ManagerPermMixin,
)

from .forms import ColleagueCreateForm, ColleagueUpdateForm
from ldap.tasks import *
from users.emails import (
    email_reopen_task,
    send_new_hire_credentials,
    send_new_hire_preboarding,
    send_reminder_email,
)
# See new_hire_views.py for new hire functions!


class ColleagueListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "colleagues.html"
    queryset = get_user_model().objects.all()
    paginate_by = 20
    ordering = ["first_name", "last_name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Colleagues")
        context["subtitle"] = _("people")
        context["slack_active"] = Integration.objects.filter(integration=0).exists()
        context["add_action"] = reverse_lazy("people:colleague_create")
        return context


class ColleagueCreateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "colleague_create.html"
    model = get_user_model()
    form_class = ColleagueCreateForm
    success_message = _("Colleague has been added")
    context_object_name = "object"
    success_url = reverse_lazy("people:colleagues")

    def form_valid(self, form):
        form.instance.is_active = False
        new_colleague = form.save()
        new_colleague=ldap_add_user(new_colleague)
        new_colleague.save()
        if settings.USER_CREDENTIALS_SEND_IMMEADIATELY:
            try:
                send_new_hire_credentials(new_colleague.id)
            except:
                pass
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create new colleague")
        context["subtitle"] = _("Employee")
        return context


class ColleagueUpdateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "colleague_update.html"
    model = get_user_model()
    form_class = ColleagueUpdateForm
    success_message = _("Employee has been updated")
    context_object_name = "object"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("Employee")
        return context


class ColleagueDeleteView(
    LoginRequiredMixin, IsAdminOrNewHireManagerMixin, SuccessMessageMixin, DeleteView
):
    queryset = get_user_model().objects.all()
    success_url = reverse_lazy("people:colleagues")
    success_message = _("Colleague has been removed")

    def form_valid(self, form):
        delete_user = self.get_object()
        ldap_delete_user(delete_user)
        messages.info(self.request, _("Colleague has been removed"))
        return super().form_valid(form)


class ColleagueResourceView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    template_name = "add_resources.html"
    model = get_user_model()
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = _("Add new resource for %(name)s") % {
            "name": new_hire.full_name
        }
        context["subtitle"] = _("Employee")
        context["object_list"] = Resource.templates.all()
        return context


class ColleagueToggleResourceView(LoginRequiredMixin, ManagerPermMixin, View):
    template_name = "_toggle_button_resources.html"

    def post(self, request, pk, template_id, *args, **kwargs):
        context = {}
        user = get_object_or_404(get_user_model(), id=pk)
        resource = get_object_or_404(Resource, id=template_id, template=True)
        if user.resources.filter(id=resource.id).exists():
            user.resources.remove(resource)
        else:
            user.resources.add(resource)
        context["id"] = id
        context["template"] = resource
        context["object"] = user
        return render(request, self.template_name, context)


class ColleagueSyncSlack(LoginRequiredMixin, ManagerPermMixin, View):
    def get(self, request, *args, **kwargs):
        slack_users = Slack().get_all_users()

        for user in slack_users:
            try:
                # Skip all bots, fake users, and people with missing profile or missing
                # email. We need to be extra careful here. Slack doesn't always respond
                # back with all info. Sometimes it might be None, an emtpy string or not
                # exist at all!
                if (
                    user["id"] == "USLACKBOT"
                    or user["is_bot"]
                    or "real_name" not in user["profile"]
                    or "email" not in user["profile"]
                    or user["profile"]["email"] == ""
                    or user["profile"]["email"] is None
                    or ("deleted" in user and user["deleted"])
                ):
                    continue

                user_info = {}

                # Get the props we need and put them into a user object
                user_props = [
                    ["first_name", "first_name"],
                    ["last_name", "last_name"],
                    ["title", "position"],
                ]
                for slack_prop, chief_prop in user_props:
                    if (
                        slack_prop in user["profile"]
                        and user["profile"][slack_prop] is not None
                    ):
                        user_info[chief_prop] = user["profile"][slack_prop]

                # If we don't have the first_name, then attempt on splitting the
                # "real_name" property. This is less accurate, as names like
                # "John van Klaas" will have three words.
                if "first_name" not in user_info:
                    split_name = user["profile"]["real_name"].split(" ", 1)
                    user_info["first_name"] = split_name[0]
                    user_info["last_name"] = (
                        "" if len(split_name) == 1 else split_name[1]
                    )

                # Find user, if email already exists, then update the user.
                # Otherwise, create the user.
                get_user_model().objects.get_or_create(
                    email=user["profile"]["email"],
                    defaults=user_info,
                )
            except Exception:
                print(f"Could not process {user['profile']['email']}")
        # Force refresh of page
        return HttpResponse(headers={"HX-Refresh": "true"})


class ColleagueGiveSlackAccessView(LoginRequiredMixin, ManagerPermMixin, View):
    template_name = "_toggle_colleague_access.html"

    def post(self, request, pk, *args, **kwargs):
        context = {}
        user = get_object_or_404(get_user_model(), pk=pk)
        context["colleague"] = user
        context["slack"] = True
        context["url_name"] = "people:connect-to-slack"

        # If Slack user already exists, then clear fields (getting disconnected)
        if user.has_slack_account:
            user.slack_user_id = ""
            user.slack_channel_id = ""
            user.save()
            context["button_name"] = _("Give access")
            return render(request, self.template_name, context)

        # If we can't find the person, then drop the request and let user know
        response = Slack().find_by_email(user.email)
        if not response:
            context["button_name"] = _("Could not find user")
            return render(request, self.template_name, context)

        # Connect slack user and send initial message
        user.slack_user_id = response["user"]["id"]
        user.save()
        translation.activate(user.language)
        blocks = [
            paragraph(
                WelcomeMessage.objects.get(
                    language=user.language, message_type=4
                ).message
            ),
            actions(
                button(
                    text=_("resources"),
                    value="show:resources",
                    style="primary",
                    action_id="show:resources",
                )
            ),
        ]

        res = Slack().send_message(blocks=blocks, channel=response["user"]["id"])
        user.slack_channel_id = res["channel"]
        user.save()

        context["button_name"] = _("Revoke Slack access")
        return render(request, self.template_name, context)


class ColleagueTogglePortalAccessView(LoginRequiredMixin, ManagerPermMixin, View):
    template_name = "_toggle_colleague_access.html"

    def post(self, request, pk, *args, **kwargs):
        context = {}
        user = get_object_or_404(get_user_model(), pk=pk, role=3)
        context["colleague"] = user
        context["url_name"] = "people:toggle-portal-access"

        user.is_active = not user.is_active
        user.save()

        if user.is_active:
            button_name = _("Revoke access")
            email_new_admin_cred(user)
        else:
            button_name = _("Give access")

        context["button_name"] = button_name
        context["exists"] = user.is_active
        return render(request, self.template_name, context)
