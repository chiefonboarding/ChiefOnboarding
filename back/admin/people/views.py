from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import (CreateView, DeleteView, FormView,
                                       UpdateView)
from django.views.generic.list import ListView

from admin.admin_tasks.models import AdminTask
from admin.notes.models import Note
from users.models import (NewHireWelcomeMessage, PreboardingUser, ResourceUser,
                          ToDoUser, User)

from .forms import ColleagueUpdateForm, NewHireAddForm, NewHireProfileForm


class NewHireListView(ListView):
    template_name = "new_hires.html"
    queryset = User.new_hires.all().order_by("-start_day")
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "New hires"
        context["subtitle"] = "people"
        context["add_action"] = reverse_lazy("people:new_hire_add")
        return context


class NewHireAddView(SuccessMessageMixin, CreateView):
    template_name = "new_hire_add.html"
    model = get_user_model()
    form_class = NewHireAddForm
    context_object_name = "object"
    success_message = "New hire has been created"
    success_url = reverse_lazy("people:new_hires")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add new hire"
        context["subtitle"] = "people"
        return context

    def form_valid(self, form):
        sequences = form.cleaned_data.pop("sequences")

        # Set new hire role
        form.instance.role = 0

        self.object = form.save()

        # Add sequences to new hire
        self.object.add_sequences(sequences)
        return super().form_valid(form)


class ColleagueListView(ListView):
    template_name = "colleagues.html"
    queryset = User.objects.all().order_by("first_name")
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Colleagues"
        context["subtitle"] = "people"
        return context


class NewHireSequenceView(DetailView):
    template_name = "new_hire_detail.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"

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

        return context


class NewHireProfileView(SuccessMessageMixin, UpdateView):
    template_name = "new_hire_profile.html"
    model = User
    form_class = NewHireProfileForm
    success_message = "New hire has been updated"
    context_object_name = "object"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class ColleagueUpdateView(SuccessMessageMixin, UpdateView):
    template_name = "colleague_update.html"
    model = User
    form_class = ColleagueUpdateForm
    success_message = "Employee has been updated"
    context_object_name = "object"

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = context["object"]
        context["title"] = new_hire.full_name
        context["subtitle"] = "Employee"
        return context


class ColleagueDeleteView(DeleteView):
    queryset = get_user_model().objects.all()
    success_url = reverse_lazy("people:colleagues")

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.info(request, "Colleague has been removed")
        return response


class NewHireNotesView(SuccessMessageMixin, CreateView):
    template_name = "new_hire_notes.html"
    model = Note
    fields = [
        "content",
    ]
    success_message = "Note has been added"

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
        context["subtitle"] = "new hire"
        context["notes"] = Note.objects.filter(new_hire=new_hire).order_by("-id")
        return context


class NewHireWelcomeMessagesView(ListView):
    template_name = "new_hire_welcome_messages.html"

    def get_queryset(self):
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        return NewHireWelcomeMessage.objects.filter(new_hire=new_hire).order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context


class NewHireAdminTasksView(TemplateView):
    template_name = "new_hire_admin_tasks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = get_object_or_404(get_user_model(), pk=self.kwargs.get("pk"))
        context["object"] = new_hire
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        context["tasks_completed"] = AdminTask.objects.filter(new_hire=new_hire, completed=True)
        context["tasks_open"] = AdminTask.objects.filter(new_hire=new_hire, completed=False)
        return context


class NewHireFormsView(DetailView):
    template_name = "new_hire_forms.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        context["preboarding_forms"] = PreboardingUser.objects.filter(user=new_hire, completed=True).exclude(form=[])
        context["todo_forms"] = ToDoUser.objects.filter(user=new_hire, completed=True).exclude(form=[])
        return context


class NewHireProgressView(DetailView):
    template_name = "new_hire_progress.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        context["resources"] = ResourceUser.objects.filter(user=new_hire, resource__course=True)
        context["todos"] = ToDoUser.objects.filter(user=new_hire)
        return context


class NewHireTasksView(DetailView):
    template_name = "new_hire_tasks.html"
    model = User
    context_object_name = "object"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_hire = self.object
        context["title"] = new_hire.full_name
        context["subtitle"] = "new hire"
        return context
