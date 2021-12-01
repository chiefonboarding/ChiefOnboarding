from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

from .forms import PreboardingForm
from .models import Preboarding


class PreboardingListView(ListView):
    template_name = "templates.html"
    queryset = Preboarding.templates.all().order_by("name")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Preboarding items"
        context["subtitle"] = "templates"
        context["add_action"] = reverse_lazy("preboarding:create")
        context["wysiwyg"] = []
        return context


class PreboardingCreateView(SuccessMessageMixin, CreateView):
    template_name = "todo_update.html"
    form_class = PreboardingForm
    success_url = reverse_lazy("preboarding:list")
    success_message = "Preboarding item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create preboarding item"
        context["subtitle"] = "templates"
        return context


class PreboardingUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "todo_update.html"
    form_class = PreboardingForm
    success_url = reverse_lazy("preboarding:list")
    queryset = Preboarding.templates.all()
    success_message = "Preboarding item has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Update preboarding item"
        context["subtitle"] = "templates"
        # context["wysiwyg"] = context["preboarding"].content_json
        return context


class PreboardingDeleteView(DeleteView):
    queryset = Preboarding.objects.all()
    success_url = reverse_lazy("preboarding:list")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Preboarding item has been removed")
        return response
