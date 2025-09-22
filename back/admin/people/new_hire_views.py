from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView, UpdateView
from django.views.generic.list import ListView
from django_q.tasks import async_task
from twilio.rest import Client

from admin.admin_tasks.models import AdminTask
from admin.integrations.forms import IntegrationExtraUserInfoForm
from admin.notes.models import Note
from admin.people.selectors import get_new_hires_for_user
from admin.sequences.models import Condition, Sequence
from admin.templates.utils import get_templates_model, get_user_field
from organization.models import Notification, Organization, WelcomeMessage
from slack_bot.slack_resource import SlackResource
from slack_bot.slack_to_do import SlackToDo
from slack_bot.tasks import link_slack_users
from slack_bot.utils import Slack, paragraph
from users.emails import (
    email_reopen_task,
    send_new_hire_credentials,
    send_new_hire_preboarding,
    send_reminder_email,
)
from users.mixins import (
    AdminOrManagerPermMixin,
    IsAdminOrNewHireManagerMixin,
    ManagerPermMixin,
)
from users.models import NewHireWelcomeMessage, PreboardingUser, ResourceUser, ToDoUser

from .forms import (
    NewHireAddForm,
    NewHireProfileForm,
    OnboardingSequenceChoiceForm,
    PreboardingSendForm,
    RemindMessageForm,
)


class NewHireListView(AdminOrManagerPermMixin, ListView):
    template_name = "new_hires.html"
    paginate_by = 10

    def get_queryset(self):
        return get_new_hires_for_user(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New hires")
        context["subtitle"] = _("people")
        context["add_action"] = reverse_lazy("people:new_hire_add")
        return context


class NewHireAddView(AdminOrManagerPermMixin, SuccessMessageMixin, CreateView):
    template_name = "new_hire_add.html"
    model = get_user_model()
    form_class = NewHireAddForm
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
        form.instance.role = get_user_model().Role.NEWHIRE

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
            async_task(
                "users.tasks.send_new_hire_credentials",
                new_hire.id,
                task_name=f"Send login credentials: {new_hire.full_name}",
            )

        # Linking user in Slack and sending welcome message (if exists)
        link_slack_users([new_hire])

        Notification.objects.create(
            notification_type=Notification.Type.ADDED_NEWHIRE,
            extra_text=new_hire.full_name,
            created_by=self.request.user,
            created_for=new_hire,
        )

        # Update user amount completed
        new_hire.update_progress()

        # Check if there are items that will not be triggered since date passed
        conditions = Condition.objects.none()
        for seq in sequences:
            if new_hire.workday == 0:
                # User has not started yet, so we only need the items before they new
                # hire started that passed
                conditions |= seq.conditions.filter(
                    condition_type=Condition.Type.BEFORE,
                    days__gte=new_hire.days_before_starting,
                )
            else:
                # user has already started, check both before start day and after for
                # conditions that are not triggered
                conditions |= seq.conditions.filter(
                    condition_type=Condition.Type.BEFORE
                ) | seq.conditions.filter(
                    condition_type=Condition.Type.AFTER, days__lte=new_hire.workday
                )

        if conditions.count():
            return render(
                self.request,
                "not_triggered_conditions.html",
                {
                    "conditions": conditions,
                    "title": new_hire.full_name,
                    "subtitle": "new hire",
                    "employee": new_hire,
                },
            )

        return super().form_valid(form)


class NewHireSendPreboardingNotificationView(IsAdminOrNewHireManagerMixin, FormView):
    template_name = "trigger_preboarding_notification.html"
    form_class = PreboardingSendForm

    def form_valid(self, form):
        new_hire = get_object_or_404(get_user_model(), id=self.kwargs.get("pk", -1))
        if form.cleaned_data["send_type"] == "email":
            send_new_hire_preboarding(new_hire, form.cleaned_data["email"])
        else:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=new_hire.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=new_hire.personalize(
                    WelcomeMessage.objects.get(
                        language=new_hire.language,
                        message_type=WelcomeMessage.Type.TEXT_WELCOME,
                    ).message
                ),
            )
        return redirect("people:new_hire", pk=new_hire.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(get_user_model(), id=user_id)
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class NewHireAddSequenceView(IsAdminOrNewHireManagerMixin, FormView):
    template_name = "new_hire_add_sequence.html"
    form_class = OnboardingSequenceChoiceForm

    def form_valid(self, form):
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(get_user_model(), id=user_id)
        sequences = Sequence.objects.filter(id__in=form.cleaned_data["sequences"])
        new_hire.add_sequences(sequences)
        messages.success(
            self.request, _("Sequence(s) have been added to this new hire")
        )

        # Check if there are items that will not be triggered since date passed
        conditions = Condition.objects.none()
        for seq in sequences:
            if new_hire.workday == 0:
                # User has not started yet, so we only need the items before they new
                # hire started that passed
                conditions |= seq.conditions.filter(
                    condition_type=Condition.Type.BEFORE,
                    days__gte=new_hire.days_before_starting,
                )
            else:
                # user has already started, check both before start day and after for
                # conditions that are not triggered
                conditions |= seq.conditions.filter(
                    condition_type=Condition.Type.BEFORE
                ) | seq.conditions.filter(
                    condition_type=Condition.Type.AFTER, days__lte=new_hire.workday
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
                    "title": new_hire.full_name,
                    "subtitle": "new hire",
                    "employee": new_hire,
                },
            )
        return redirect("people:new_hire", pk=new_hire.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk", -1)
        new_hire = get_object_or_404(get_user_model(), id=user_id)
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class NewHireRemoveSequenceView(IsAdminOrNewHireManagerMixin, View):
    def post(self, request, pk, sequence_pk, *args, **kwargs):
        sequence = get_object_or_404(Sequence, id=sequence_pk)
        new_hire = get_object_or_404(get_user_model(), id=pk)
        new_hire.remove_sequence(sequence)

        # Update user amount and completed
        new_hire.update_progress()

        messages.success(request, _("Sequence items were removed from this new hire"))

        return redirect("people:new_hire", pk=new_hire.id)


class NewHireTriggerConditionView(IsAdminOrNewHireManagerMixin, TemplateView):
    template_name = "_trigger_sequence_items.html"

    def post(self, request, pk, condition_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=condition_pk)
        new_hire = get_object_or_404(get_user_model(), id=pk)
        condition.process_condition(new_hire, skip_notification=True)

        # Update user amount completed
        new_hire.update_progress()

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        condition_id = self.kwargs.get("condition_pk", -1)
        condition = get_object_or_404(Condition, id=condition_id)
        context["completed"] = True
        context["condition"] = condition
        # not relevant, still needed for processing the template
        context["employee"] = get_object_or_404(
            get_user_model(), id=self.kwargs.get("pk")
        )
        return context


class NewHireSendLoginEmailView(IsAdminOrNewHireManagerMixin, View):
    def post(self, request, pk, *args, **kwargs):
        new_hire = get_object_or_404(get_user_model(), id=pk)
        send_new_hire_credentials(new_hire.id)
        messages.success(request, _("Sent email to new hire"))
        return redirect("people:new_hire", pk=new_hire.id)


class NewHireSequenceView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_detail.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")

        conditions = new_hire.conditions.prefetched()

        # condition items
        context["conditions"] = (
            (
                conditions.filter(
                    condition_type=2, days__lte=new_hire.days_before_starting
                )
                | conditions.filter(
                    condition_type=Condition.Type.AFTER, days__gte=new_hire.workday
                )
                | conditions.filter(condition_type=Condition.Type.TODO)
                | conditions.filter(condition_type=Condition.Type.ADMIN_TASK)
            )
            .alias_days_order()
            .order_by("days_order")
        )

        context["notifications"] = Notification.objects.filter(
            created_for=new_hire
        ).select_related("created_by")

        context["completed_todos"] = ToDoUser.objects.filter(
            user=new_hire, completed=True
        ).values_list("to_do__pk", flat=True)
        context["completed_admin_tasks"] = AdminTask.objects.filter(
            new_hire=new_hire, completed=True
        ).values_list("based_on__pk", flat=True)
        return context


class NewHireProfileView(SuccessMessageMixin, IsAdminOrNewHireManagerMixin, UpdateView):
    template_name = "new_hire_profile.html"
    model = get_user_model()
    form_class = NewHireProfileForm
    success_message = _("New hire has been updated")

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireMigrateToNormalAccountView(IsAdminOrNewHireManagerMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(
            get_user_model(), id=pk, role=get_user_model().Role.NEWHIRE
        )
        user.role = 3
        user.save()
        messages.info(request, _("New hire is now a normal account."))
        return redirect("people:new_hires")


class NewHireExtraInfoUpdateView(
    UpdateView,
    IsAdminOrNewHireManagerMixin,
    SuccessMessageMixin,
):
    template_name = "token_create.html"
    form_class = IntegrationExtraUserInfoForm
    queryset = get_user_model().new_hires.all()
    success_message = _("Extra info has been added!")

    def get_success_url(self):
        user = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        return reverse("people:new_hire", args=[user.id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["button_text"] = _("Update")
        return context


class NewHireNotesView(
    IsAdminOrNewHireManagerMixin,
    SuccessMessageMixin,
    CreateView,
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
        context["notes"] = (
            Note.objects.filter(new_hire=new_hire)
            .order_by("-id")
            .select_related("admin")
        )
        return context


class NewHireWelcomeMessagesView(IsAdminOrNewHireManagerMixin, ListView):
    template_name = "new_hire_welcome_messages.html"

    def get_queryset(self):
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        return (
            NewHireWelcomeMessage.objects.filter(new_hire=new_hire)
            .order_by("-id")
            .select_related("colleague")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireAdminTasksView(IsAdminOrNewHireManagerMixin, TemplateView):
    template_name = "new_hire_admin_tasks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["tasks_completed"] = AdminTask.objects.filter(
            new_hire=new_hire, completed=True
        ).select_related("new_hire", "assigned_to")
        context["tasks_open"] = AdminTask.objects.filter(
            new_hire=new_hire, completed=False
        ).select_related("new_hire", "assigned_to")
        return context


class NewHireFormsView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_forms.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["preboarding_forms"] = (
            PreboardingUser.objects.filter(user=new_hire, form__isnull=False)
            .exclude(form=[])
            .defer("preboarding__content")
        )
        context["todo_forms"] = (
            ToDoUser.objects.filter(user=new_hire, completed=True)
            .exclude(form=[])
            .select_related("to_do")
            .defer("to_do__content")
        )
        return context


class NewHireProgressView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_progress.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["resources"] = ResourceUser.objects.filter(
            user=new_hire, resource__course=True
        )
        context["todos"] = (
            ToDoUser.objects.filter(user=new_hire)
            .select_related("to_do")
            .only("completed", "to_do__name", "to_do__id")
        )
        return context


class NewHireRemindView(IsAdminOrNewHireManagerMixin, View):
    def post(self, request, pk, template_type, template_pk, *args, **kwargs):
        if template_type not in ["todouser", "resourceuser"]:
            raise Http404

        template_user_model = apps.get_model("users", template_type)

        template_user_obj = template_user_model.objects.get(pk=template_pk)
        template_user_obj.reminded = timezone.now()
        template_user_obj.save()

        translation.activate(template_user_obj.user.language)
        if template_user_obj.user.has_slack_account:
            if template_type == "todouser":
                block = SlackToDo(template_user_obj, template_user_obj.user).get_block()
            else:
                block = SlackResource(
                    template_user_obj, template_user_obj.user
                ).get_block()

            Slack().send_message(
                blocks=[paragraph(_("Don't forget this item!")), block],
                channel=template_user_obj.user.slack_user_id,
            )
        else:
            send_reminder_email(template_user_obj.object_name, template_user_obj.user)

        # Revert language as reminder should be sent in admin language
        translation.activate(request.user.language)
        messages.success(self.request, _("Reminder has been sent!"))

        return redirect("people:new_hire_progress", pk=template_user_obj.user.id)


class NewHireReopenTaskView(IsAdminOrNewHireManagerMixin, FormView):
    template_name = "new_hire_reopen_task.html"
    form_class = RemindMessageForm

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            template_type = self.kwargs.get("template_type", "")
            if template_type not in ["todouser", "resourceuser"]:
                raise Http404

        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        template_pk = self.kwargs.get("template_pk", -1)
        template_type = self.kwargs.get("template_type", "")

        template_user_model = apps.get_model("users", template_type)

        template_user_obj = template_user_model.objects.get(pk=template_pk)
        if template_type == "todouser":
            template_user_obj.completed = False
            template_user_obj.form = []
        else:
            template_user_obj.completed_course = False
            template_user_obj.step = 0
            template_user_obj.answers.clear()

        template_user_obj.save()

        translation.activate(template_user_obj.user.language)
        if template_user_obj.user.has_slack_account:
            if template_type == "todouser":
                block = SlackToDo(template_user_obj, template_user_obj.user).get_block()
            else:
                block = SlackResource(
                    template_user_obj, template_user_obj.user
                ).get_block()

            Slack().send_message(
                blocks=[paragraph(form.cleaned_data["message"]), block],
                text=form.cleaned_data["message"],
                channel=template_user_obj.user.slack_user_id,
            )
        else:
            email_reopen_task(
                template_user_obj.object_name,
                form.cleaned_data["message"],
                template_user_obj.user,
            )

        # Revert language as reminder should be sent in admin language
        translation.activate(self.request.user.language)
        messages.success(self.request, _("Item has been reopened"))

        # Update user amount completed
        template_user_obj.user.update_progress()

        return redirect("people:new_hire_progress", pk=template_user_obj.user.id)


class NewHireCourseAnswersView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_course_answers.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = _("new hire")
        context["resource_user"] = get_object_or_404(
            ResourceUser, user=new_hire, pk=self.kwargs.get("resource_user", -1)
        )
        return context


class NewHireTasksView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_tasks.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.object.full_name
        context["subtitle"] = _("new hire")
        return context


class NewHireTaskListView(IsAdminOrNewHireManagerMixin, DetailView):
    template_name = "new_hire_add_task.html"
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        templates_model = get_templates_model(self.kwargs.get("type", ""))
        if templates_model is None:
            raise Http404

        context["title"] = _("Add/Remove templates for %(name)s") % {
            "name": self.object.full_name
        }
        context["subtitle"] = _("new hire")
        context["object_list"] = templates_model.templates.all()
        context["user_items"] = getattr(
            self.object, get_user_field(self.kwargs.get("type", ""))
        ).values_list("id", flat=True)
        return context


class NewHireToggleTaskView(IsAdminOrNewHireManagerMixin, TemplateView):
    template_name = "_toggle_button_new_hire_template.html"

    def post(self, request, pk, template_id, type):
        user = get_object_or_404(get_user_model(), id=pk)
        templates_model = get_templates_model(type)

        if templates_model is None:
            raise Http404

        template = get_object_or_404(templates_model, id=template_id, template=True)
        user_items = getattr(user, get_user_field(type))
        if user_items.filter(id=template.id).exists():
            user_items.remove(template)
        else:
            user_items.add(template)

        user_items = user_items.values_list("id", flat=True)
        # Update user amount completed
        user.update_progress()

        context = self.get_context_data(
            **{
                "template": template,
                "user_items": user_items,
                "object": user,
                "id": id,
                "template_type": type,
            }
        )
        return self.render_to_response(context)


class NewHireDeleteView(IsAdminOrNewHireManagerMixin, SuccessMessageMixin, DeleteView):
    template_name = "new_hire_delete.html"
    queryset = get_user_model().new_hires.all()
    success_url = reverse_lazy("people:new_hires")
    success_message = _("New hire has been removed")


class CompleteAdminTaskView(IsAdminOrNewHireManagerMixin, DetailView):
    def post(self, request, pk, admin_task_pk, *args, **kwargs):
        task = get_object_or_404(AdminTask, id=admin_task_pk)
        task.mark_completed()

        messages.success(request, _("The admin task was successfully completed"))

        return redirect("people:new_hire_admin_tasks", pk=pk)
