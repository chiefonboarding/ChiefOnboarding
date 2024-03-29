from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.translation import gettext as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView
from django_q.tasks import async_task
from rest_framework import generics
from rest_framework.authentication import SessionAuthentication

from admin.admin_tasks.models import AdminTask
from admin.hardware.models import Hardware
from admin.integrations.exceptions import (
    DataIsNotJSONError,
    FailedPaginatedResponseError,
    KeyIsNotInDataError,
)
from admin.integrations.models import Integration
from admin.integrations.sync_userinfo import SyncUsers
from admin.people.serializers import UserImportSerializer
from admin.resources.models import Resource
from admin.sequences.models import Condition, Sequence
from api.permissions import AdminPermission
from organization.models import Organization, WelcomeMessage
from slack_bot.utils import Slack, actions, button, paragraph
from users.emails import email_new_admin_cred
from users.mixins import (
    AdminPermMixin,
    IsAdminOrNewHireManagerMixin,
    LoginRequiredMixin,
    ManagerPermMixin,
)
from users.models import ToDoUser

from .forms import (
    ColleagueCreateForm,
    ColleagueUpdateForm,
    EmailIgnoreForm,
    OffboardingSequenceChoiceForm,
    UserRoleForm,
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
        context["slack_active"] = Integration.objects.filter(
            integration=Integration.Type.SLACK_BOT
        ).exists()
        context["import_users_options"] = Integration.objects.import_users_options()
        context["add_action"] = reverse_lazy("people:colleague_create")
        return context


class OffboardingColleagueListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    template_name = "offboarding.html"
    queryset = get_user_model().offboarding.all()
    paginate_by = 20
    ordering = ["termination_date", "email"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Employees who are about to leave the company")
        context["subtitle"] = _("people")
        return context


class ColleagueCreateView(
    LoginRequiredMixin, ManagerPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "colleague_create.html"
    model = get_user_model()
    form_class = ColleagueCreateForm
    success_message = _("Colleague has been added")
    success_url = reverse_lazy("people:colleagues")

    def form_valid(self, form):
        form.instance.is_active = False
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

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("Employee")
        return context


class ColleagueHardwareView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    template_name = "add_hardware.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = context["object"]
        context["title"] = _("Add new hardware for %(name)s") % {"name": user.full_name}
        context["subtitle"] = _("Employee")
        context["object_list"] = Hardware.templates.all()
        return context


class ColleagueToggleHardwareView(LoginRequiredMixin, ManagerPermMixin, View):
    template_name = "_toggle_button_hardware.html"

    def post(self, request, pk, template_id, *args, **kwargs):
        context = {}
        user = get_object_or_404(get_user_model(), id=pk)
        hardware = get_object_or_404(Hardware, id=template_id, template=True)
        if user.hardware.filter(id=hardware.id).exists():
            user.hardware.remove(hardware)
        else:
            user.hardware.add(hardware)
        context["id"] = id
        context["template"] = hardware
        context["object"] = user
        return render(request, self.template_name, context)


class ColleagueResourceView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    template_name = "add_resources.html"
    model = get_user_model()

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
                    language=user.language,
                    message_type=WelcomeMessage.Type.SLACK_KNOWLEDGE,
                ).message
            ),
            actions(
                [
                    button(
                        text=_("resources"),
                        value="show_resource_items",
                        style="primary",
                        action_id="show_resource_items",
                    )
                ]
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
        user = get_object_or_404(
            get_user_model(), pk=pk, role=get_user_model().Role.OTHER
        )
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


class AddOffboardingSequenceView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "add_offboarding_sequence.html"
    form_class = OffboardingSequenceChoiceForm
    model = get_user_model()

    def dispatch(self, *args, **kwargs):
        # raise "login required" before 404
        if self.request.user.is_authenticated:
            employee = self.get_object()
            if employee.termination_date is not None:
                raise Http404
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.full_name
        context["subtitle"] = _("Employee")
        return context

    def form_valid(self, form):
        sequence_ids = form.cleaned_data.pop("sequences", [])
        form.save()
        employee = self.object
        # delete all previous conditions (from being a new hire)
        employee.conditions.all().delete()

        # TODO: should become a background worker at some point
        for integration in Integration.objects.filter(
            manifest_type=Integration.ManifestType.WEBHOOK,
            manifest__exists__isnull=False,
        ):
            integration.user_exists(employee)

        sequences = Sequence.offboarding.filter(id__in=sequence_ids)
        employee.add_sequences(sequences)

        # Check if there are items that will not be triggered since date passed
        conditions = Condition.objects.none()
        for seq in sequences:
            conditions |= seq.conditions.filter(
                condition_type=Condition.Type.BEFORE,
                days__gte=employee.days_before_termination_date,
            )

        if conditions.count():
            # Prefetch records to avoid a massive amount of queries
            conditions = Condition.objects.prefetched().filter(
                id__in=conditions.values_list("pk", flat=True)
            )
            return render(
                self.request,
                "not_triggered_conditions.html",
                {
                    "conditions": conditions,
                    "title": employee.full_name,
                    "subtitle": "Employee",
                    "employee": employee,
                },
            )
        return redirect("people:colleagues")


class ColleagueOffboardingSequenceView(
    LoginRequiredMixin, IsAdminOrNewHireManagerMixin, DetailView
):
    template_name = "offboarding_detail.html"
    queryset = get_user_model().offboarding.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = self.object
        context["title"] = employee.full_name
        context["subtitle"] = _("Offboarding")

        conditions = employee.conditions.prefetched()

        # condition items
        context["conditions"] = (
            (
                conditions.filter(
                    condition_type=Condition.Type.BEFORE,
                    days__lte=employee.days_before_termination_date,
                )
                | conditions.filter(condition_type=Condition.Type.TODO)
                | conditions.filter(condition_type=Condition.Type.ADMIN_TASK)
            )
            .alias_days_order()
            .order_by("days_order")
        )

        context["completed_todos"] = ToDoUser.objects.filter(
            user=employee, completed=True
        ).values_list("to_do__pk", flat=True)
        context["completed_admin_tasks"] = AdminTask.objects.filter(
            new_hire=employee, completed=True
        ).values_list("based_on__pk", flat=True)
        return context


class ColleagueImportView(LoginRequiredMixin, AdminPermMixin, DetailView):
    """Generic view to start showing the options based on what it fetched from the
    server
    """

    template_name = "colleague_import.html"
    context_object_name = "integration"

    def get_queryset(self):
        return Integration.objects.import_users_options()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subtitle"] = _("Import new users from a third party")
        context["title"] = _("Import people")
        return context


class ColleagueImportFetchUsersHXView(LoginRequiredMixin, AdminPermMixin, View):
    """HTMLX view to get all users and return a table"""

    def get(self, request, pk, *args, **kwargs):
        integration = get_object_or_404(
            Integration.objects.import_users_options(), id=pk
        )
        try:
            # we are passing in the user who is requesting it, but we likely don't need
            # them.
            users = SyncUsers(integration).get_import_user_candidates()
        except (
            KeyIsNotInDataError,
            FailedPaginatedResponseError,
            DataIsNotJSONError,
        ) as e:
            return render(request, "_import_user_table.html", {"error": e})

        return render(
            request,
            "_import_user_table.html",
            {"users": users, "role_form": UserRoleForm},
        )


class ColleagueImportIgnoreUserHXView(LoginRequiredMixin, AdminPermMixin, View):
    """HTMLX view to put people on the ignore list"""

    def post(self, request, *args, **kwargs):
        form = EmailIgnoreForm(request.POST)
        # We always expect an email here, if it's not, then all data is likely incorrect
        # as we specifically call "email" from the API
        if form.is_valid():
            org = Organization.objects.get()
            org.ignored_user_emails += [form.cleaned_data["email"]]
            org.save()

        return HttpResponse()


class ColleagueImportAddUsersView(LoginRequiredMixin, generics.CreateAPIView):
    permission_classes = (AdminPermission,)
    authentication_classes = [
        SessionAuthentication,
    ]
    serializer_class = UserImportSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        users = serializer.save()

        # users is a list, so manually checking instead of filter queryset
        for user in users:
            if user.is_admin_or_manager:
                async_task(email_new_admin_cred, user)
            else:
                # if they are not admin or manager, then they are a normal user
                # don't allow them to login
                user.is_active = False
                user.save()

        success_message = _(
            "Users got imported succesfully. "
            "Admins and managers will receive an email shortly."
        )
        return HttpResponse(
            f"<div class='alert alert-success'><p>{success_message}</p></div>"
        )
