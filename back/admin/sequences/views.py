from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.integrations.forms import IntegrationConfigForm
from admin.integrations.models import Integration
from admin.sequences.utils import get_sequence_model_form, get_sequence_templates_model
from admin.templates.utils import get_templates_model
from admin.to_do.models import ToDo
from users.mixins import LoginRequiredMixin, ManagerPermMixin

from .forms import (
    ConditionCreateForm,
    ConditionUpdateForm,
    PendingEmailMessageForm,
    PendingSlackMessageForm,
    PendingTextMessageForm,
)
from .models import (
    Condition,
    ExternalMessage,
    IntegrationConfig,
    Sequence,
)


class SequenceListView(LoginRequiredMixin, ManagerPermMixin, ListView):
    """
    Lists all sequences in a table.
    """

    template_name = "templates.html"
    queryset = Sequence.objects.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Sequence items")
        context["subtitle"] = ""
        context["add_action"] = reverse_lazy("sequences:create")
        return context


class SequenceCreateView(LoginRequiredMixin, ManagerPermMixin, RedirectView):
    """
    Creates a new sequences, also adds a default (empty) sequence for unconditional
    items. Redirects user back to the newly created sequence.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        seq = Sequence.objects.create(name="New sequence")
        seq.conditions.create(condition_type=3)
        return seq.update_url()


class SequenceView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    """
    Shows one sequence to the user. This includes a list of `ToDo` items for on the
    right side (the others will be loaded on click).
    """

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
        context["conditions"] = obj.conditions.prefetched().order_by("id")
        return context


class SequenceNameUpdateView(LoginRequiredMixin, ManagerPermMixin, UpdateView):
    """
    Updates the name of the sequence when the user ends typing.

    HTMX view.
    """

    template_name = "_sequence_templates_list.html"
    model = Sequence
    fields = [
        "name",
    ]
    # fake page, we don't need to report back
    success_url = "/health"


class SequenceConditionCreateView(LoginRequiredMixin, ManagerPermMixin, CreateView):
    """
    Add a new condition block to the sequence.
    When valid, it will reload the sequence timeline to make sure everything is in
    the correct order.

    HTMX view
    """

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


class SequenceConditionUpdateView(LoginRequiredMixin, ManagerPermMixin, UpdateView):
    """
    Update a condition block in the sequence.
    When valid, it will reload the sequence timeline to make sure everything is in
    the correct order.

    HTMX view
    """

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


class SequenceTimelineDetailView(LoginRequiredMixin, ManagerPermMixin, DetailView):
    """
    Renders the sequence timeline.
    HTMX view, this will only get called when the frontend requests an updated view.
    On: added condition block, updated condition block, adding a template to the
    condition
    """

    template_name = "_sequence_timeline.html"
    model = Sequence

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context["conditions"] = obj.conditions.prefetched().order_by("id")
        context["todos"] = ToDo.templates.all()
        return context


class SequenceFormView(LoginRequiredMixin, ManagerPermMixin, View):
    """
    Get form when clicking on a line in a condition or dragging non-template, either
    empty or filled in form.

    HTMX view, this will only get called when the frontend requests a form.
    """

    def get(self, request, template_type, template_pk, *args, **kwargs):

        # Get a filled custom form based on integration config model
        if template_type == "integrationconfig":
            template_item = get_object_or_404(IntegrationConfig, id=template_pk)
            form = template_item.integration.config_form(template_item.additional_data)
            return render(
                request,
                "_item_form.html",
                {"form": form},
            )

        form = get_sequence_model_form(template_type)

        if form is None:
            raise Http404

        template_item = None
        # If template_pk is 0, then it shows an empty form
        if template_pk != 0:
            templates_model = get_sequence_templates_model(template_type)
            template_item = get_object_or_404(templates_model, id=template_pk)

        # Get a EMPTY custom form (depending on what provision) when it's an integration
        # config like Slack, Asana, Google...
        if form == IntegrationConfigForm:
            form = template_item.config_form()
            return render(
                request,
                "_item_form.html",
                {"form": form},
            )

        return render(
            request, "_item_form.html", {"form": form(instance=template_item)}
        )


class SequenceFormUpdateView(LoginRequiredMixin, ManagerPermMixin, View):
    """
    Update or create a specific line item (template or not) in a condition item (excl.
    Integration config)

    :params str template_type: i.e. todo, resource, introduction
    :params int template_pk: the pk of the used template (0 if none)
    :params int condition: the pk of the condition (can never be 0)

    HTMX view, this will only get called when the frontend requests to update an item.
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
        # Check if original item was template or doesn't exist (is new), if so, then
        # create new
        if template_item is None or (
            hasattr(template_item, "template") and template_item.template
        ):
            item_form = form(request.POST)
        else:
            item_form = form(instance=template_item, data=request.POST)

        if item_form.is_valid():
            obj = item_form.save(commit=False)
            obj.template = False
            obj.save()

            # Check if new item has been created. If it has, then remove the old
            # record and add the new one. If it hasn't created a new object, then
            # the old one is good enough.
            if obj.id != template_pk:
                condition = get_object_or_404(Condition, id=condition)

                # This can probably be cleaned up, we can't use proxy object. We need
                # the base one
                if form in [
                    PendingEmailMessageForm,
                    PendingSlackMessageForm,
                    PendingTextMessageForm,
                ]:
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


class SequenceFormUpdateIntegrationConfigView(
    LoginRequiredMixin, ManagerPermMixin, View
):
    """
    This will update or create an integration config object

    :params str template_type: always `integrationconfig`
    :params int template_pk: either of `Integration` or `IntegrationConfig` depending if
    object exists (see exists param)
    :params int condition: the pk of the condition (can never be 0)
    :params int exists: either 1 or 0 - basically boolean

    HTMX view, this will only get called when the frontend requests to update or create
    a integration config item.
    """

    def post(
        self, request, template_type, template_pk, condition, exists, *args, **kwargs
    ):

        condition = get_object_or_404(Condition, id=condition)
        if exists == 0:
            # If this provision item does not exist yet, then create one
            integration = get_object_or_404(Integration, id=template_pk)
            form_class = integration.config_form
            existing_item = None
        else:
            # If this provision item exist, then get it, so we can update it
            existing_item = get_object_or_404(IntegrationConfig, id=template_pk)
            form_class = existing_item.integration.config_form

        item_form = form_class(request.POST)

        # if form is not valid, push back form with errors
        if not item_form.is_valid():
            return render(request, "_item_form.html", {"form": item_form})

        # Either create a provision item or update it
        if existing_item is None:
            integration_config = IntegrationConfig.objects.create(
                integration=integration,
                additional_data=item_form.cleaned_data,
            )
            condition.add_item(integration_config)
        else:
            existing_item.additional_data = item_form.cleaned_data
            existing_item.save()

        # Succesfully created/updated item, reload the sequence
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})


class SequenceConditionItemView(LoginRequiredMixin, ManagerPermMixin, View):
    """
    This will delete or add a template item to a condition

    :params int pk: Condition pk
    :params string type: template type, i.e. todo, resource...
    :params int template_pk: the pk of object in the template type

    HTMX view, this will only get called when the frontend requests to add or delete
    a template to a sequence (drag/drop).
    """

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
        condition = Condition.objects.filter(id=condition.id).prefetched().first()
        return render(
            request,
            "_sequence_condition.html",
            {"condition": condition, "object": condition.sequence, "todos": todos},
        )


class SequenceConditionDeleteView(LoginRequiredMixin, ManagerPermMixin, View):
    """
    Delete an entire condition

    :params int pk: Sequence pk
    :params int condition_pk: Condition pk

    HTMX view, the cross in a condition
    """

    def delete(self, request, pk, condition_pk, *args, **kwargs):
        sequence = get_object_or_404(Sequence, id=pk)
        condition = get_object_or_404(Condition, id=condition_pk, sequence=sequence)
        # Can never delete the unconditioned condition
        if condition.condition_type == 3:
            raise Http404
        condition.delete()
        return HttpResponse()


class SequenceDeleteView(LoginRequiredMixin, ManagerPermMixin, DeleteView):
    """
    Delete an entire sequence

    :params int pk: Sequence pk
    """

    queryset = Sequence.objects.all()
    success_url = reverse_lazy("sequences:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, _("Sequence item has been removed"))
        return response


class SequenceDefaultTemplatesView(LoginRequiredMixin, ManagerPermMixin, ListView):
    """
    Get a list of all available template items to drop in the sequence

    :params str type: the template type

    HTMX view, whenever clicked on any of the template icons on the right side
    of the screen
    """

    template_name = "_sequence_templates_list.html"

    def get_queryset(self):
        template_type = self.request.GET.get("type", "")
        if template_type == "integration":
            return Integration.objects.sequence_integration_options()

        if get_templates_model(template_type) is None:
            # if type does not exist, then return empty queryset
            return Sequence.objects.none()

        templates_model = get_templates_model(template_type)
        return templates_model.templates.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = self.request.GET.get("type", "")
        return context
