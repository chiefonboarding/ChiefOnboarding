from datetime import timedelta

from axes.decorators import axes_dispatch
from django.contrib import messages
from django.contrib.auth import get_user_model, login, signals
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from admin.resources.models import Chapter, CourseAnswer, Resource
from organization.models import Notification
from users.mixins import LoginRequiredMixin
from users.models import (NewHireWelcomeMessage, PreboardingUser, ResourceUser,
                          ToDoUser, User)

from .forms import QuestionsForm


class NewHireDashboard(LoginRequiredMixin, TemplateView):
    template_name = "new_hire_to_dos.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        new_hire = self.request.user
        context = super().get_context_data(**kwargs)

        context["overdue_to_do_items"] = ToDoUser.objects.filter(
            user=new_hire, to_do__due_on_day__lt=new_hire.workday(), completed=False
        )

        to_do_items = ToDoUser.objects.filter(
            user=new_hire, to_do__due_on_day__gte=new_hire.workday()
        )

        # Group items by amount work days
        items_by_date = []
        for to_do_user in to_do_items:
            # Check if to do is already in any of the new items_by_date
            to_do = to_do_user.to_do
            if not any(
                [item for item in items_by_date if item["day"] == to_do.due_on_day]
            ):
                new_date = {
                    "day": to_do.due_on_day,
                    "items": [
                        to_do,
                    ],
                }
                items_by_date.append(new_date)
            else:
                # Can never be two or more, since it's catching it if it already exists
                existing_date = [
                    item for item in items_by_date if item["day"] == to_do.due_on_day
                ][0]
                existing_date["items"].append(to_do_user)

        # Convert days to date object
        for obj in items_by_date:
            obj["date"] = self.request.user.start_day + timedelta(days=obj["day"] - 1)

        context["to_do_items"] = items_by_date

        context["title"] = _("Things you need to do")
        context["subtitle"] = _("Tasks")
        return context


class ToDoDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_to_do.html"
    model = ToDoUser


@method_decorator(axes_dispatch, name="dispatch")
class PreboardingShortURLRedirectView(LoginRequiredMixin, RedirectView):
    pattern_name = "new_hire:preboarding"

    def dispatch(self, *args, **kwargs):
        try:
            user = User.objects.get(
                unique_url=self.request.GET.get("token", ""),
                start_day__gte=timezone.now(),
                role=0,
            )
        except User.DoesNotExist:
            # Log wrong keys by ip to prevent guessing/bruteforcing
            signals.user_login_failed.send(
                sender=User,
                request=self.request,
                credentials={
                    "token": self.request.GET.get("token", ""),
                },
            )
            raise Http404
        except:
            # fail safe
            raise Http404

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(self.request, user)
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        preboarding_user = PreboardingUser.objects.filter(
            user=self.request.user
        ).order_by("order")
        return reverse("new_hire:preboarding", args=[preboarding_user.first().id])


class PreboardingDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_preboarding.html"
    model = PreboardingUser

    def dispatch(self, *args, **kwargs):
        # Make sure user is authenticated to view this object
        if self.request.user.is_authenticated:
            get_object_or_404(PreboardingUser, user=self.request.user, id=kwargs["pk"])
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preboarding_user_items = list(
            PreboardingUser.objects.filter(user=self.request.user)
            .order_by("order")
            .values_list("id", flat=True)
        )
        index_current_item = preboarding_user_items.index(self.object.id)

        # Add new hire welcome messages to first page
        if (
            index_current_item == 0
            and NewHireWelcomeMessage.objects.filter(
                new_hire=self.request.user
            ).exists()
        ):
            context["welcome_messages"] = NewHireWelcomeMessage.objects.filter(
                new_hire=self.request.user
            )

        # Check that current item is not last, otherwise push first
        if self.object.id != preboarding_user_items[-1]:
            next_id = preboarding_user_items[index_current_item + 1]
            button_text = "Next"
        else:
            button_text = "Restart"
            next_id = preboarding_user_items[0]

        context["button_text"] = button_text
        context["next_id"] = next_id
        return context


class ColleagueListView(LoginRequiredMixin, ListView):
    template_name = "new_hire_colleagues.html"
    model = User
    paginate_by = 20
    ordering = ["first_name", "last_name"]


class ColleagueSearchView(LoginRequiredMixin, ListView):
    template_name = "_new_hire_colleagues_search.html"
    model = User

    def get_queryset(self):
        search = self.request.GET.get("search", "")
        return get_user_model().objects.filter(
            Q(first_name__icontains=search), Q(last_name__icontains=search)
        )


class ResourceListView(LoginRequiredMixin, ListView):
    template_name = "new_hire_resources.html"
    paginate_by = 20

    def get_queryset(self):
        return ResourceUser.objects.filter(user=self.request.user).order_by(
            "resource__category"
        )


class ResourceDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_resource_detail.html"
    model = Resource

    def dispatch(self, *args, **kwargs):
        # Make sure it's either a course or if it's a course the user is not skipping items
        if self.request.user.is_authenticated:
            resource_user = get_object_or_404(
                ResourceUser,
                user=self.request.user,
                resource__id=self.kwargs.get("pk", -1),
            )
            # Early return if not course
            if not resource_user.resource.course:
                return super().dispatch(*args, **kwargs)

            # Check if user is allowed to see the requested chapter otherwise raise 404
            # User should only be allowed to see the next chapter and previous ones
            chapter = get_object_or_404(Chapter, id=self.kwargs.get("chapter", -1))
            if chapter.order > resource_user.step + 1:
                raise Http404

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resource_user"] = get_object_or_404(
            ResourceUser, user=self.request.user, resource__id=self.kwargs.get("pk", -1)
        )
        context["chapter"] = get_object_or_404(
            Chapter, id=self.kwargs.get("chapter", -1)
        )
        context["title"] = context["resource_user"].resource.name
        # chapter is questions tab, so add form if not filled in yet
        if (
            context["chapter"].type == 2
            and not context["resource_user"]
            .answers.filter(chapter=context["chapter"])
            .exists()
        ):
            context["form"] = QuestionsForm(items=context["chapter"].content["blocks"])
        return context


class ToDoCompleteView(LoginRequiredMixin, RedirectView):
    pattern_name = "new_hire:to_do"

    def get_redirect_url(self, *args, **kwargs):
        to_do_user = get_object_or_404(
            ToDoUser, pk=kwargs["pk"], user=self.request.user
        )
        to_do_user.completed = True
        to_do_user.save()

        Notification.objects.create(
            notification_type="completed_todo",
            extra_text=to_do_user.todo.name,
            created_by=self.request.user,
        )
        return super().get_redirect_url(*args, **kwargs)


class CourseNextStepView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        resource_user = get_object_or_404(ResourceUser, pk=pk, user=request.user)
        chapter = resource_user.add_step()

        if chapter is None:
            messages.success(request, _("You have completed this course!"))
            Notification.objects.create(
                notification_type="completed_course",
                extra_text=resource_user.resource.name,
                created_by=self.request.user,
            )
            return redirect("new_hire:resources")

        return redirect(
            "new_hire:resource-detail", pk=resource_user.resource.id, chapter=chapter.id
        )


class CourseAnswerView(LoginRequiredMixin, FormView):
    template_name = "_question_form.html"
    form_class = QuestionsForm

    def get_form(self, form_class=None):
        """
        Return an instance of the form to be used in this view.
        Adding chapter form arguments
        """
        chapter = get_object_or_404(Chapter, id=self.kwargs.get("chapter", -1))
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(items=chapter.content["blocks"], **self.get_form_kwargs())

    def form_valid(self, form):
        resource_user = get_object_or_404(
            ResourceUser, resource__pk=self.kwargs.get("pk", -1), user=self.request.user
        )
        chapter = get_object_or_404(Chapter, id=self.kwargs.get("chapter", -1))
        course_answers = CourseAnswer.objects.create(
            chapter=chapter, answers=form.cleaned_data
        )
        resource_user.answers.add(course_answers)
        return HttpResponse(headers={"HX-Refresh": "true"})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = get_object_or_404(Resource, id=self.kwargs.get("pk", -1))
        context["chapter"] = get_object_or_404(
            Chapter, id=self.kwargs.get("chapter", -1)
        )
        return context
