from django.contrib import messages
from django.db.models import Prefetch, Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.integrations.models import AccessToken
from admin.sequences.utils import get_sequence_model_form, get_sequence_templates_model
from admin.templates.utils import get_model_form, get_templates_model
from admin.to_do.models import ToDo
from admin.resources.models import Resource
from admin.preboarding.models import Preboarding
from admin.badges.models import Badge
from admin.appointments.models import Appointment
from admin.introductions.models import Introduction
from users.mixins import AdminPermMixin, LoginRequiredMixin

from .forms import ConditionCreateForm, ConditionToDoUpdateForm, ConditionUpdateForm, AccountProvisionForm, PendingTextMessageForm, PendingSlackMessageForm, PendingEmailMessageForm
from .models import Condition, Sequence, ExternalMessage, AccountProvision, PendingAdminTask



class SequenceListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Sequence.objects.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Sequence items")
        context["subtitle"] = ""
        context["add_action"] = reverse_lazy("sequences:create")
        return context


class SequenceCreateView(LoginRequiredMixin, AdminPermMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        seq = Sequence.objects.create(name="New sequence")
        seq.conditions.create(condition_type=3)
        return seq.update_url()


class SequenceView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "sequence.html"
    model = Sequence

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Sequence")
        context["subtitle"] = ""
        context["object_list"] = ToDo.templates.all().defer("content")
        context["condition_form"] = ConditionCreateForm()
        context["todos"] = ToDo.templates.all().defer("content")
        obj = self.get_object()
        context["conditions"] = (
            obj.conditions
            .prefetch_related(
                Prefetch("introductions", queryset=Introduction.objects.all()),
                Prefetch("to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("resources", queryset=Resource.objects.all()),
                Prefetch("appointments", queryset=Appointment.objects.all().defer("content")),
                Prefetch("badges", queryset=Badge.objects.all().defer("content")),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_new_hire().defer("content", "content_json"), to_attr='external_new_hire'),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_admins().defer("content", "content_json"), to_attr='external_admin'),
                Prefetch("condition_to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("admin_tasks", queryset=PendingAdminTask.objects.all()),
                Prefetch("preboarding", queryset=Preboarding.objects.all().defer("content")),
                Prefetch("account_provisions", queryset=AccountProvision.objects.all()),
            ).order_by("id")
        )
        return context


class SequenceNameUpdateView(LoginRequiredMixin, AdminPermMixin, UpdateView):
    template_name = "_sequence_templates_list.html"
    model = Sequence
    fields = [
        "name",
    ]
    # fake page, we don't need to report back
    success_url = "/health"


class SequenceConditionCreateView(LoginRequiredMixin, AdminPermMixin, CreateView):
    template_name = "_condition_form.html"
    model = Condition
    form_class = ConditionCreateForm
    # fake page, we don't need to report back
    success_url = "/health"

    def form_valid(self, form):
        # add condition to sequence
        sequence = get_object_or_404(Sequence, pk=self.kwargs.get("pk", -1))
        form.instance.sequence = sequence
        form.save()
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(Sequence, pk=self.kwargs.get("pk", -1))
        context["condition_form"] = context["form"]
        context["todos"] = ToDo.templates.all()
        return context


class SequenceConditionUpdateView(LoginRequiredMixin, AdminPermMixin, UpdateView):
    template_name = "_condition_form.html"
    model = Condition
    form_class = ConditionUpdateForm
    # fake page, we don't need to report back
    success_url = "/health"

    def form_valid(self, form):
        form.save()
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(
            Sequence, pk=self.kwargs.get("sequence_pk", -1)
        )
        context["condition_form"] = context["form"]
        return context


class SequenceTimelineDetailView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "_sequence_timeline.html"
    model = Sequence

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["conditions"] = (
            obj.conditions
            .prefetch_related(
                Prefetch("introductions", queryset=Introduction.objects.all()),
                Prefetch("to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("resources", queryset=Resource.objects.all()),
                Prefetch("appointments", queryset=Appointment.objects.all().defer("content")),
                Prefetch("badges", queryset=Badge.objects.all().defer("content")),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_new_hire().defer("content", "content_json"), to_attr='external_new_hire'),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_admins().defer("content", "content_json"), to_attr='external_admin'),
                Prefetch("condition_to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("admin_tasks", queryset=PendingAdminTask.objects.all()),
                Prefetch("preboarding", queryset=Preboarding.objects.all().defer("content")),
                Prefetch("account_provisions", queryset=AccountProvision.objects.all()),
            ).order_by("id")
        )
        context["todos"] = ToDo.templates.all()
        return context


class SequenceFormView(LoginRequiredMixin, AdminPermMixin, View):
    """
    Get item when clicking on a line in a condition, either empty or filled in form
    """
    def get(self, request, template_type, template_pk, *args, **kwargs):

        form = get_sequence_model_form(template_type)

        if form is None:
            raise Http404

        template_item = None
        if template_pk != 0:
            templates_model = get_sequence_templates_model(template_type)
            template_item = get_object_or_404(templates_model, id=template_pk)

        if form == AccountProvisionForm:
            form = template_item.access_token.add_user_form_class()
            return render(
                request, "_item_form.html", {"form": form(template_item.additional_data)}
            )

        return render(
            request, "_item_form.html", {"form": form(instance=template_item)}
        )


class SequenceFormUpdateView(LoginRequiredMixin, AdminPermMixin, View):
    """
    This will update or create a specific line item (template or not) in a condition item (excl. Account provision)
    """

    def post(self, request, template_type, template_pk, condition, *args, **kwargs):

        # Get form, if it doesn't exist, then 404
        form = get_sequence_model_form(template_type)
        if form is None:
            raise Http404

        # Get template item if id was not 0. 0 means that it doesn't exist
        template_item = None
        if template_pk != 0:
            templates_model = get_sequence_templates_model(template_type)
            template_item = get_object_or_404(templates_model, id=template_pk)

        # Push instance and data through form and save it
        # Check if original item was template or doesn't exist (is new), if so, then create new
        if template_item is None or (hasattr(template_item, "template") and template_item.template):
            item_form = form(request.POST)
        else:
            item_form = form(instance=template_item, data=request.POST)

        if item_form.is_valid():
            obj = item_form.save(commit=False)
            obj.template = False
            obj.save()

            # Check if new item has been created. If it has, then remove the old record and add the new one.
            # If it hasn't created a new object, then the old one is good enough.
            if obj.id != template_pk:
                condition = get_object_or_404(Condition, id=condition)

                # This can probably be cleaned up, we can't use proxy object. We need the base one
                if form in [PendingEmailMessageForm, PendingSlackMessageForm, PendingTextMessageForm]:
                    obj = ExternalMessage.objects.get(id=obj.id)

                condition.add_item(obj)
                # Delete the old item, if there is one
                if template_item is not None:
                    condition.remove_item(template_item)

        else:
            # Form is not valid, push back form with errors
            return render(request, "_item_form.html", {"form": item_form})

        # Succesfully created/updated item, request sequence reload
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})


class SequenceFormUpdateAccountProvisionView(LoginRequiredMixin, AdminPermMixin, View):
    """
    This will update or create an account provision object
    """

    def post(self, request, template_type, template_pk, condition, exists, *args, **kwargs):

        condition = get_object_or_404(Condition, id=condition)
        if exists == 0:
            access_token = get_object_or_404(AccessToken, id=template_pk)
            form_class = access_token.add_user_form_class()
            existing_item = None
        else:
            existing_item = get_object_or_404(AccountProvision, id=template_pk)
            form_class = existing_item.access_token.add_user_form_class()

        item_form = form_class(request.POST)

        if not item_form.is_valid():
            # Form is not valid, push back form with errors
            return render(request, "_item_form.html", {"form": item_form})

        if existing_item is None:
            account_provision = AccountProvision.objects.create(integration_type=access_token.account_provision_name, additional_data=item_form.cleaned_data)
            condition.add_item(account_provision)
        else:
            existing_item.additional_data = item_form.cleaned_data
            existing_item.save()

        # Succesfully created/updated item
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})


class SequenceConditionItemView(LoginRequiredMixin, AdminPermMixin, View):
    """This will delete or add a template item to a condition"""

    def delete(self, request, pk, type, template_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=pk)
        templates_model = get_sequence_templates_model(type)
        template_item = get_object_or_404(templates_model, id=template_pk)
        condition.remove_item(template_item)
        return HttpResponse()

    def post(self, request, pk, type, template_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=pk)
        templates_model = get_templates_model(type)
        template_item = get_object_or_404(templates_model, id=template_pk)
        condition.add_item(template_item)
        todos = ToDo.templates.all()
        condition = (
            Condition.objects.filter(id=condition.id).prefetch_related(
                Prefetch("introductions", queryset=Introduction.objects.all()),
                Prefetch("to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("resources", queryset=Resource.objects.all()),
                Prefetch("appointments", queryset=Appointment.objects.all().defer("content")),
                Prefetch("badges", queryset=Badge.objects.all().defer("content")),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_new_hire().defer("content", "content_json"), to_attr='external_new_hire'),
                Prefetch("external_messages", queryset=ExternalMessage.objects.for_admins().defer("content", "content_json"), to_attr='external_admin'),
                Prefetch("condition_to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("admin_tasks", queryset=PendingAdminTask.objects.all()),
                Prefetch("preboarding", queryset=Preboarding.objects.all().defer("content")),
                Prefetch("account_provisions", queryset=AccountProvision.objects.all()),
            ).first()
        )
        return render(
            request,
            "_sequence_condition.html",
            {"condition": condition, "object": condition.sequence, "todos": todos},
        )


class SequenceConditionToDoUpdateView(LoginRequiredMixin, AdminPermMixin, UpdateView):
    """
    This will update the conditions of a trigger based on a ToDo item.
    """

    template_name = "_sequence_condition.html"
    model = Condition
    form_class = ConditionToDoUpdateForm

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["condition"] = obj
        context["object"] = obj.sequence
        context["todos"] = ToDo.templates.all()
        return context


class SequenceConditionDeleteView(LoginRequiredMixin, AdminPermMixin, View):
    """Delete an entire condition"""

    def delete(self, request, pk, condition_pk, *args, **kwargs):
        sequence = get_object_or_404(Sequence, id=pk)
        condition = get_object_or_404(Condition, id=condition_pk, sequence=sequence)
        # Can never delete the unconditioned condition
        if condition.condition_type == 3:
            raise Http404
        condition.delete()
        return HttpResponse()


class SequenceDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Condition.objects.all()
    success_url = reverse_lazy("sequences:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("Sequence item has been removed"))
        return response


class SequenceDefaultTemplatesView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "_sequence_templates_list.html"

    def get_queryset(self):
        template_type = self.request.GET.get("type", "")
        if template_type == "accountprovision":
            return AccessToken.objects.account_provision_options()

        if get_templates_model(template_type) is None:
            # if type does not exist, then return empty queryset
            return Sequence.objects.none()

        templates_model = get_templates_model(template_type)
        return templates_model.templates.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = self.request.GET.get("type", "")
        return context
