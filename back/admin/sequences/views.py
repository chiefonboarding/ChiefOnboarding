from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from admin.integrations.models import AccessToken
from admin.people.utils import get_model_form, get_templates_model, get_user_field
from admin.to_do.models import ToDo
from users.mixins import AdminPermMixin, LoginRequiredMixin

from .emails import send_sequence_message
from .forms import ConditionCreateForm, ConditionToDoUpdateForm, ConditionUpdateForm
from .models import Condition, ExternalMessage, PendingAdminTask, Sequence


class SequenceListView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "templates.html"
    queryset = Sequence.objects.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Sequence items"
        context["subtitle"] = ""
        context["add_action"] = reverse_lazy("sequences:create")
        return context


class SequenceCreateView(LoginRequiredMixin, AdminPermMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        seq = Sequence.objects.create(name="New sequence")
        return seq.update_url()


class SequenceView(LoginRequiredMixin, AdminPermMixin, DetailView):
    template_name = "sequence.html"
    model = Sequence

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Sequence"
        context["subtitle"] = ""
        context["object_list"] = ToDo.templates.all()
        context["condition_form"] = ConditionCreateForm()
        context["todos"] = ToDo.templates.all()
        obj = self.get_object()
        context["conditions_unconditioned"] = obj.conditions.get(condition_type=3)
        context["conditions_before_first_day"] = obj.conditions.filter(condition_type=2)
        context["conditions_after_first_day"] = obj.conditions.filter(condition_type=0)
        context["conditions_based_on_todo"] = obj.conditions.filter(condition_type=1)
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
        context["conditions_unconditioned"] = obj.conditions.get(condition_type=3)
        context["conditions_before_first_day"] = obj.conditions.filter(condition_type=2)
        context["conditions_after_first_day"] = obj.conditions.filter(condition_type=0)
        context["conditions_based_on_todo"] = obj.conditions.filter(condition_type=1)
        context["todos"] = ToDo.templates.all()
        return context


class SequenceFormView(LoginRequiredMixin, AdminPermMixin, View):
    def get(self, request, template_type, template_pk, *args, **kwargs):

        form = get_model_form(template_type)
        if form is None:
            raise Http404

        template_item = None
        if template_pk != 0:
            templates_model = get_templates_model(template_type)
            template_item = get_object_or_404(templates_model, id=template_pk)

        return render(
            request, "_item_form.html", {"form": form(instance=template_item)}
        )


class SequenceFormUpdateView(LoginRequiredMixin, AdminPermMixin, View):
    def post(self, request, template_type, template_pk, condition, *args, **kwargs):

        # Get form, if it doesn't exist, then 404
        form = get_model_form(template_type)
        if form is None:
            raise Http404

        # Get template item if id was not 0. 0 means that it doesn't exist
        template_item = None
        if template_pk != 0:
            templates_model = get_templates_model(template_type)
            template_item = get_object_or_404(templates_model, id=template_pk)

        # Push instance and data through form and save it
        # Check if original item was template, if so, then create new
        if template_item.template:
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
                condition.remove_item(template_item)
                condition.add_item(obj)

        else:
            # Form has valid, push back form with errors
            return render(request, "_item_form.html", {"form": item_form})

        # Succesfully created/updated item, request sequence reload
        return HttpResponse(headers={"HX-Trigger": "reload-sequence"})


class SequenceConditionItemView(LoginRequiredMixin, AdminPermMixin, View):
    def delete(self, request, pk, type, template_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=pk)
        templates_model = get_templates_model(type)
        template_item = get_object_or_404(templates_model, id=template_pk)
        condition.remove_item(template_item)
        return HttpResponse()

    def post(self, request, pk, type, template_pk, *args, **kwargs):
        condition = get_object_or_404(Condition, id=pk)
        templates_model = get_templates_model(type)
        template_item = get_object_or_404(templates_model, id=template_pk)
        condition.add_item(template_item)
        todos = ToDo.templates.all()
        return render(
            request,
            "_sequence_condition.html",
            {"condition": condition, "object": condition.sequence, "todos": todos},
        )


class SequenceConditionToDoUpdateView(LoginRequiredMixin, AdminPermMixin, UpdateView):
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
    def delete(self, request, pk, condition_pk, *args, **kwargs):
        sequence = get_object_or_404(Sequence, id=pk)
        condition = get_object_or_404(Condition, id=condition_pk, sequence=sequence)
        if condition.condition_type == 3:
            raise Http404
        condition.delete()
        return HttpResponse()


class SequenceDeleteView(LoginRequiredMixin, AdminPermMixin, DeleteView):
    queryset = Condition.objects.all()
    success_url = reverse_lazy("sequences:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Sequence item has been removed")
        return response


class SequenceDefaultTemplatesView(LoginRequiredMixin, AdminPermMixin, ListView):
    template_name = "_sequence_templates_list.html"

    def get_queryset(self):
        template_type = self.request.GET.get("type", "")
        if template_type == "account_provision":
            return AccessToken.objects.filter(active=True)

        if get_templates_model(template_type) is None:
            # if type does not exist, then return None
            return Sequence.objects.none()

        templates_model = get_templates_model(template_type)
        return templates_model.templates.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active"] = self.request.GET.get("type", "")
        return context


# class SendTestMessage(APIView):
#     def post(self, request, id):
#         ext_message = ExternalMessage.objects.select_related("send_to").prefetch_related("content_json").get(id=id)
#         if ext_message.send_via == 0:  # email
#             send_sequence_message(request.user, ext_message.email_message(), ext_message.subject)
#         elif ext_message.send_via == 1:  # slack
#             # User is not connected to slack. Needs -> employees -> 'give access'
#             if request.user.slack_channel_id == None:
#                 return Response({"slack": "not exist"}, status=status.HTTP_400_BAD_REQUEST)
#             s = Slack()
#             s.set_user(request.user)
#             blocks = []
#             for j in ext_message.content_json.all():
#                 blocks.append(j.to_slack_block(request.user))
#             s.send_message(blocks=blocks)
#         return Response()


# class SaveAdminTask(APIView):
#     def post(self, request):
#         if "id" in request.data:
#             pending_admin_task = PendingAdminTask.objects.select_related("assigned_to").get(id=request.data["id"])
#             pending_task = PendingAdminTaskSerializer(pending_admin_task, data=request.data, partial=True)
#         else:
#             pending_task = PendingAdminTaskSerializer(data=request.data)
#         pending_task.is_valid(raise_exception=True)
#         pending_task.save()
#         return Response(pending_task.data)
