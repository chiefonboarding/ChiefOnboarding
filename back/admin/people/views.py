from datetime import datetime, timedelta

from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView
from django_q.tasks import async_task
from twilio.rest import Client

from admin.admin_tasks.models import AdminTask
from admin.integrations.models import AccessToken
from admin.notes.models import Note
from admin.resources.models import Resource
from admin.sequences.models import Condition, Sequence
from admin.templates.utils import get_templates_model
from organization.models import Organization, WelcomeMessage, Notification
from slack_bot.slack import Slack
from slack_bot.tasks import link_slack_users
from users.emails import (
    email_new_admin_cred,
    email_reopen_task,
    send_new_hire_credentials,
    send_new_hire_preboarding,
    send_reminder_email,
)
from users.mixins import AdminPermMixin, LoginRequiredMixin
from users.models import (
    NewHireWelcomeMessage,
    PreboardingUser,
    ResourceUser,
    ToDoUser,
    User,
)

from .forms import (
    ColleagueCreateForm,
    ColleagueUpdateForm,
    NewHireAddForm,
    NewHireProfileForm,
    PreboardingSendForm,
    RemindMessageForm,
    SequenceChoiceForm,
)


class NewHireListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "new_hires.html"
    paginate_by = 10

    def get_queryset(self):
        all_new_hires = get_user_model().new_hires.all().order_by("-start_day")
        if self.request.user.is_admin:
            return all_new_hires
        return all_new_hires.filter(manager=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New hires")
        context["subtitle"] = _("people")
        context["add_action"] = reverse_lazy("people:new_hire_add")
        return context


class NewHireAddView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "new_hire_add.html"
    model = get_user_model()
    form_class = NewHireAddForm
    context_object_name = "object"
    success_message = _("New hire has been created")
    success_url = reverse_lazy("people:new_hires")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Add new hire")
        context["subtitle"] = _("people")
        return context

    def form_valid(self, form):
        sequences = form.cleaned_data.pop("sequences")

        # Set new hire role
        form.instance.role = 0

        new_hire = form.save()

        # Add sequences to new hire
        new_hire.add_sequences(sequences)

        # Send credentials email if the user was created after their start day
        org = Organization.object.get()
        new_hire_datetime = new_hire.get_local_time()
        if (
            new_hire_datetime.date() >= new_hire.start_day
            and new_hire_datetime.hour >= 7
            and new_hire_datetime.weekday() < 5
            and org.new_hire_email
        ):
            async_task("users.tasks.send_new_hire_credentials", new_hire.id)

        # Linking user in Slack and sending welcome message (if exists)
        link_slack_users([new_hire])

        Notification.objects.create(
            notification_type='added_new_hire',
            extra_text=new_hire.full_name,
            created_by=self.request.user
        )

        return super().form_valid(form)


class NewHireSendPreboardingNotificationView(
    LoginRequiredMixin, AdminPermMixin, FormView
):
    template_name = "trigger_preboarding_notification.html"
    form_class = PreboardingSendForm

    def form_valid(self, form):
        new_hire = get_object_or_404(User, id=self.kwargs.get("pk", -1))
        if form.cleaned_data["send_type"] == "email":
            send_new_hire_preboarding(new_hire)
        else:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=new_hire.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=new_hire.personalize(
                    WelcomeMessage.objects.get(
                        language=new_hire.language, message_type=2
                    ).message
                ),
            )
        return redirect("people:new_hire", pk=new_hire.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(User, id=user_id)
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class NewHireAddSequenceView(LoginRequiredMixin, AdminPermMixin, FormView):
    template_name = "new_hire_add_sequence.html"
    form_class = SequenceChoiceForm

    def form_valid(self, form):
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(User, id=user_id)
        sequences = Sequence.objects.filter(id__in=form.cleaned_data["sequences"])
        new_hire.add_sequences(sequences)
        messages.success(self.request, _("Sequence(s) have been added to this new hire"))

        # Check if there are items that will not be triggered since date passed
        conditions = Condition.objects.none()
        for seq in sequences:
            if new_hire.workday() == 0:
                # User has not started yet, so we only need the items before they new hire started that passed
                conditions = conditions | seq.conditions.filter(
                    condition_type=2, days__lte=new_hire.days_before_starting()
                )
            else:
                # user has already started, check both before start day and after for conditions that are not triggered
                conditions = seq.conditions.filter(
                    condition_type=2
                ) | seq.conditions.filter(
                    condition_type=0, days__lte=new_hire.workday()
                )

        if conditions.count():
            return render(
                self.request,
                "not_triggered_conditions.html",
                {
                    "conditions": conditions,
                    "title": new_hire.full_name,
                    "subtitle": "new hire",
                    "new_hire_id": new_hire.id,
                },
            )
        return redirect("people:new_hire", pk=new_hire.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(User, id=user_id)
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class NewHireTriggerConditionView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "_trigger_sequence_items.html"

    def get(self, request, pk, condition_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=condition_pk)
        new_hire = get_object_or_404(User, id=pk)
        condition.process_condition(new_hire)

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        condition_id = self.kwargs.get("condition_pk", -1)
        condition = get_object_or_404(Condition, id=condition_id)
        context["completed"] = True
        context["condition"] = condition
        # not relevant, still needed for processing the template
        context["new_hire_id"] = 0
        return context


class NewHireSendLoginEmailView(LoginRequiredMixin, AdminPermMixin, View):
    def get(self, request, pk, *args, **kwargs):
        new_hire = get_object_or_404(User, id=pk)
        send_new_hire_credentials(new_hire)
        messages.success(request, _("Sent email to new hire"))
        return redirect("people:new_hire", pk=new_hire.id)


class ColleagueListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "colleagues.html"
    queryset = User.objects.all().order_by("first_name")
    paginate_by = 20
    ordering = ["first_name", "last_name"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Colleagues")
        context["subtitle"] = _("people")
        context["slack_active"] = AccessToken.objects.filter(integration=0).exists()
        context["add_action"] = reverse_lazy("people:colleague_create")
        return context


class NewHireSequenceView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_detail.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")

        # condition items
        conditions_before_first_day = new_hire.conditions.filter(
            condition_type=2, days__lte=new_hire.days_before_starting()
        )
        conditions_after_first_day = new_hire.conditions.filter(
            condition_type=0, days__lte=new_hire.days_before_starting()
        )
        for condition in conditions_before_first_day:
            condition.days = new_hire.start_day - timedelta(days=condition.days)

        for condition in conditions_after_first_day:
            condition.days = new_hire.start_day + timedelta(days=condition.days)

        context["conditions_before_first_day"] = conditions_before_first_day
        context["conditions_after_first_day"] = conditions_after_first_day

        context["notifications"] = Notification.objects.filter(created_for=new_hire)
        return context


class NewHireProfileView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "new_hire_profile.html"
    model = User
    form_class = NewHireProfileForm
    success_message = _("New hire has been updated")
    context_object_name = "object"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        return context


class ColleagueUpdateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, UpdateView
):
    template_name = "colleague_update.html"
    model = User
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


class ColleagueCreateView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "colleague_create.html"
    model = User
    form_class = ColleagueCreateForm
    success_message = _("Colleague has been added")
    context_object_name = "object"
    success_url = reverse_lazy("people:colleagues")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Create new colleague")
        context["subtitle"] = _("Employee")
        return context


class ColleagueToggleResourceView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "_toggle_button_resources.html"

    def get_context_data(self, pk, template_id, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(get_user_model(), id=pk)
        resource = get_object_or_404(Resource, id=template_id)
        if user.resources.filter(id=resource.id).exists():
            user.resources.remove(resource)
        else:
            user.resources.add(resource)
        context["id"] = id
        context["template"] = resource
        context["object"] = user
        return context


class ColleagueResourceView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "add_resources.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = _("Add new resource for %(name)") % {'name': new_hire.full_name}
        context["subtitle"] = _("Employee")
        context["object_list"] = Resource.objects.all()
        return context


class ColleagueDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = get_user_model().objects.all()
    success_url = reverse_lazy("people:colleagues")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("Colleague has been removed"))
        return response


class NewHireDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    template_name = "new_hire_delete.html"
    queryset = get_user_model().objects.all()
    success_url = reverse_lazy("people:new_hires")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("New hire has been removed"))
        return response


class NewHireMigrateToNormalAccountView(LoginRequiredMixin, AdminPermMixin, View):
    queryset = get_user_model().objects.all()
    success_url = reverse_lazy("people:new_hires")

    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(get_user_model(), id=pk)
        user.role = 3
        user.save()
        messages.info(request, _("New hire is now a normal account."))
        return redirect("people:new_hires")


class NewHireNotesView(
    LoginRequiredMixin, AdminPermMixin, SuccessMessageMixin, CreateView
):
    template_name = "new_hire_notes.html"
    model = Note
    fields = [
        "content",
    ]
    success_message = _("Note has been added")

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        form.instance.admin = self.request.user
        form.instance.new_hire = new_hire
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["notes"] = Note.objects.filter(new_hire=new_hire).order_by("-id")
        return context


class NewHireWelcomeMessagesView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "new_hire_welcome_messages.html"

    def get_queryset(self):
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        return NewHireWelcomeMessage.objects.filter(new_hire=new_hire).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireAdminTasksView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "new_hire_admin_tasks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["tasks_completed"] = AdminTask.objects.filter(
            new_hire=new_hire, completed=True
        )
        context["tasks_open"] = AdminTask.objects.filter(
            new_hire=new_hire, completed=False
        )
        return context


class NewHireFormsView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_forms.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["preboarding_forms"] = PreboardingUser.objects.filter(
            user=new_hire, completed=True
        ).exclude(form=[])
        context["todo_forms"] = ToDoUser.objects.filter(
            user=new_hire, completed=True
        ).exclude(form=[])
        return context


class NewHireProgressView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_progress.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["resources"] = ResourceUser.objects.filter(
            user=new_hire, resource__course=True
        )
        context["todos"] = ToDoUser.objects.filter(user=new_hire)
        return context


class NewHireRemindView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request, pk, template_type, *args, **kwargs):
        if template_type not in ["todouser", "resourceuser"]:
            raise Http404

        template_user_model = apps.get_model("users", template_type)

        template_user_obj = template_user_model.objects.get(pk=pk)
        template_user_obj.reminded = datetime.now()
        template_user_obj.save()

        if template_user_obj.user.has_slack_account:
            s = Slack()
            s.set_user(template_user_obj.user)

            if template_type == "todouser":
                blocks = s.format_to_do_block(
                    pre_message=_("Don't forget this to do item!"),
                    items=[template_user_obj],
                )
            else:
                blocks = s.format_resource_block(
                    pre_message=_("Don't forget to complete this course!"),
                    items=[template_user_obj],
                )

            s.send_message(blocks=blocks)
        else:
            send_reminder_email(template_user_obj)

        messages.success(self.request, _("Reminder has been sent!"))

        return redirect("people:new_hire_progress", pk=template_user_obj.user.id)


class NewHireReopenTaskView(LoginRequiredMixin, AdminPermMixin, FormView):
    template_name = "new_hire_reopen_task.html"
    form_class = RemindMessageForm

    def form_valid(self, form):
        template_type = self.kwargs.get("template_type", "")
        pk = self.kwargs.get("pk", -1)

        if template_type not in ["todouser", "resourceuser"]:
            raise Http404

        template_user_model = apps.get_model("users", template_type)

        template_user_obj = template_user_model.objects.get(pk=pk)
        if template_type == "todouser":
            template_user_obj.completed = False
            template_user_obj.form = []
        else:
            template_user_obj.completed_course = False
            template_user_obj.answers.clean()

        template_user_obj.save()

        if template_user_obj.user.has_slack_account:
            s = Slack()
            s.set_user(template_user_obj.user)

            if template_type == "todouser":
                blocks = s.format_to_do_block(
                    pre_message=form.cleaned_data["message"], items=[template_user_obj]
                )
            else:
                blocks = s.format_resource_block(
                    pre_message=form.cleaned_data["message"],
                    items=[template_user_obj],
                )

            s.send_message(blocks=blocks)
        else:
            email_reopen_task(
                template_user_obj, form.cleaned_data["message"], template_user_obj.user
            )

        messages.success(self.request, _("Item has been reopened"))

        return redirect("people:new_hire_progress", pk=template_user_obj.user.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template_type = self.kwargs.get("template_type", "")
        pk = self.kwargs.get("pk", -1)

        if template_type not in ["todouser", "resourceuser"]:
            raise Http404

        template_user_model = apps.get_model("users", template_type)
        template_user_obj = template_user_model.objects.get(pk=pk)
        context["title"] = template_user_obj.user.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireCourseAnswersView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_course_answers.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["resource_user"] = get_object_or_404(
            ResourceUser, user=new_hire, pk=self.kwargs.get("resource_user", -1)
        )
        return context


class NewHireTasksView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_tasks.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireAccessView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_access.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["loading"] = True
        context["integrations"] = AccessToken.objects.account_provision_options()
        return context


class NewHireCheckAccessView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "_new_hire_access_card.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        integration = get_object_or_404(
            AccessToken, id=self.kwargs.get("integration_id", -1)
        )
        found_user = integration.api_class().find_by_email(new_hire.email)
        context["integration"] = integration
        context["active"] = found_user
        return context


class NewHireGiveAccessView(LoginRequiredMixin, AdminPermMixin, FormView):
    template_name = "give_new_hire_access.html"

    def get_form_class(self):
        integration = get_object_or_404(
            AccessToken, id=self.kwargs.get("integration_id", -1)
        )
        return integration.add_user_form_class()

    def form_valid(self, form):
        new_hire = get_object_or_404(User, id=self.kwargs.get("pk", -1))
        integration = get_object_or_404(
            AccessToken, id=self.kwargs.get("integration_id", -1)
        )
        # TODO: make this async
        integration.add_user(new_hire.email, form.cleaned_data)

        return redirect("people:new_hire_access", pk=new_hire.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(User, id=self.kwargs.get("pk", -1))
        integration = get_object_or_404(
            AccessToken, id=self.kwargs.get("integration_id", -1)
        )
        context["integration"] = integration
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["new_hire"] = new_hire
        return context


class NewHireTaskListView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "new_hire_add_task.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        templates_model = get_templates_model(self.kwargs.get("type", ""))
        if templates_model is None:
            raise Http404

        context["title"] = _("Add/Remove templates for %(name)") % {'name': self.object.full_name}
        context["subtitle"] = _("new hire")
        context["object_list"] = templates_model.templates.all()
        context["user_items"] = getattr(
            self.object, get_user_field(self.kwargs.get("type", ""))
        )
        return context


class NewHireToggleTaskView(LoginRequiredMixin, AdminPermMixin, TemplateView):
    template_name = "_toggle_button_new_hire_template.html"

    def get_context_data(self, pk, template_id, type, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(get_user_model(), id=pk)
        templates_model = get_templates_model(type)
        if templates_model is None:
            raise Http404

        template = get_object_or_404(templates_model, id=template_id)
        user_items = getattr(user, get_user_field(type))
        if user_items.filter(id=template.id).exists():
            user_items.remove(template)
        else:
            user_items.add(template)
        context["id"] = id
        context["template"] = template
        context["user_items"] = user_items
        context["object"] = user
        context["template_type"] = type
        return context


class ColleagueSyncSlack(LoginRequiredMixin, AdminPermMixin, View):
    def get(self, request, *args, **kwargs):
        slack_users = Slack().get_all_users()

        for user in slack_users:
            # Skip all bots, fake users, and people with missing profile or missing email
            # We need to be extra careful here. Slack doesn't always respond back with all info
            # Sometimes it might be None, an emtpy string or not exist at all!
            if (
                user["id"] == "USLACKBOT"
                or user["is_bot"]
                or "real_name" not in user["profile"]
                or "email" not in user["profile"]
                or user["profile"]["email"] == ""
                or user["profile"]["email"] == None
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

            # If we don't have the first_name, then attempt on splitting the "real_name" property.
            # This is less accurate, as names like "John van Klaas" will have three words.
            if "first_name" not in user_info:
                split_name = user["profile"]["real_name"].split(" ", 1)
                user_info["first_name"] = split_name[0]
                user_info["last_name"] = "" if len(split_name) == 1 else split_name[1]

            # Find user, if email already exists, then update the user.
            # Otherwise, create the user.
            get_user_model().objects.get_or_create(
                email=user["profile"]["email"],
                defaults=user_info,
            )
        # Force refresh of page
        return HttpResponse(headers={"HX-Refresh": "true"})


class ColleagueGiveSlackAccessView(LoginRequiredMixin, AdminPermMixin, View):
    template_name = "_toggle_colleague_access.html"

    def post(self, request, pk, *args, **kwargs):
        context = {}
        user = get_object_or_404(User, pk=pk)
        context["colleague"] = user
        context["slack"] = True
        context["url_name"] = "people:connect-to-slack"

        if user.slack_user_id != "":
            user.slack_user.id = ""
            user.slack_channel_id = ""
            user.save()
            context["button_name"] = _("Give access")
            return render(request, self.template_name, context)

        s = Slack()
        response = s.find_by_email(user.email)
        if not response:
            context["button_name"] = _("Could not find user")
            return render(request, self.template_name, context)

        user.slack_user_id = response["user"]["id"]
        user.save()
        translation.activate(user.language)
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _(
                        "Click on the button to see all the categories that are available to you!"
                    ),
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": _("resources")},
                        "style": "primary",
                        "value": "show:resources",
                    }
                ],
            },
        ]
        s.set_user(user)
        res = s.send_message(blocks=blocks)
        user.slack_channel_id = res["channel"]
        user.save()

        button_name = _("Revoke Slack access")
        if user.slack_channel_id == "":
            button_name = _("Give access")

        context["button_name"] = button_name
        return render(request, self.template_name, context)


class ColleagueTogglePortalAccessView(LoginRequiredMixin, AdminPermMixin, View):
    template_name = "_toggle_colleague_access.html"

    def post(self, request, pk, *args, **kwargs):
        context = {}
        user = get_object_or_404(User, pk=pk)
        context["colleague"] = user
        context["url_name"] = "people:toggle-portal-access"

        user.is_active = not user.is_active
        user.save()

        if user.is_active:
            button_name = _("Revoke access")
            exists = True
            email_new_admin_cred(user)
        else:
            button_name = _("Give portal access")
            exists = False

        context["button_name"] = button_name
        context["exists"] = exists
        return render(request, self.template_name, context)
