from datetime import datetime

from axes.decorators import axes_dispatch
from django.contrib import messages
from django.contrib.auth import get_user_model, login, signals
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from admin.resources.models import Chapter, CourseAnswer, Resource
from admin.to_do.models import ToDo
from organization.models import Notification
from users.mixins import LoginRequiredMixin
from users.models import (
    NewHireWelcomeMessage,
    PreboardingUser,
    ResourceUser,
    ToDoUser,
    User,
)

from .forms import QuestionsForm


class NewHireDashboard(LoginRequiredMixin, TemplateView):
    template_name = "new_hire_to_dos.html"

    def get_context_data(self, **kwargs):
        new_hire = self.request.user

        # Check that user is allowed to see page (only new hires)
        if new_hire.role != get_user_model().Role.NEWHIRE:
            raise Http404

        context = super().get_context_data(**kwargs)

        context["overdue_to_do_items"] = ToDoUser.objects.overdue(new_hire)

        to_do_items = (
            ToDoUser.objects.filter(
                user=new_hire, to_do__due_on_day__gte=new_hire.workday
            )
            .select_related("to_do")
            .defer("to_do__content")
        )

        # Group items by amount work days
        items_by_date = []
        for to_do_user in to_do_items:
            # Check if to do day is already in any of the new items_by_date
            to_do = to_do_user.to_do
            if not any(
                [item for item in items_by_date if item["day"] == to_do.due_on_day]
            ):
                new_date = {
                    "day": to_do.due_on_day,
                    "items": [
                        to_do_user,
                    ],
                }
                items_by_date.append(new_date)
            else:
                # If it does exist, then add it to the array of that type
                existing_dates = [
                    item for item in items_by_date if item["day"] == to_do.due_on_day
                ]
                # Can never be more than one, since it's catching it if it already
                # exists
                existing_dates[0]["items"].append(to_do_user)

        # Convert days to date object
        for obj in items_by_date:
            obj["date"] = self.request.user.workday_to_datetime(obj["day"])

        context["to_do_items"] = items_by_date

        context["title"] = _("Things you need to do")
        context["subtitle"] = _("Tasks")
        return context


class ToDoDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_to_do.html"

    def get_queryset(self):
        return ToDoUser.objects.filter(user=self.request.user)


class ToDoCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        to_do_user = get_object_or_404(ToDoUser, pk=pk, user=self.request.user)
        to_do_user.mark_completed()

        Notification.objects.create(
            notification_type=Notification.Type.COMPLETED_TODO,
            extra_text=to_do_user.to_do.name,
            created_by=request.user,
        )
        return redirect("new_hire:todos")


class FormSubmitView(LoginRequiredMixin, View):
    """
    HTMX: Submit form that user filled in
    """

    def post(self, request, pk, type, *args, **kwargs):
        if type == "to_do":
            item_user = get_object_or_404(ToDoUser, pk=pk, user=self.request.user)
            form_items = item_user.to_do.form_items
        else:
            item_user = get_object_or_404(
                PreboardingUser, pk=pk, user=self.request.user
            )
            form_items = item_user.preboarding.form_items

        answers = item_user.form
        for key, value in request.POST.items():
            # check if item is valid
            item = next((x for x in form_items if x["id"] == key), None)
            if item is not None:
                item["answer"] = value
                answers.append(item)
            else:
                return HttpResponse(
                    _("This form could not be processed - invalid items")
                )

        item_user.form = answers
        item_user.save()

        return HttpResponse(_("You have submitted this form successfully"))


class SeenUpdatesView(LoginRequiredMixin, View):
    """
    When user click on the notification icon to list all notifications, it will update
    the last seen updates prop. This way, the red marker on the notification icon will
    go away.
    """

    def get(self, request, *args, **kwargs):
        request.user.seen_updates = datetime.now()
        request.user.save()
        return HttpResponse()


@method_decorator(axes_dispatch, name="dispatch")
class SlackToDoFormView(LoginRequiredMixin, TemplateView):
    template_name = "slack_form.html"

    def dispatch(self, *args, **kwargs):
        try:
            user = User.objects.get(
                unique_url=self.request.GET.get("token", ""),
                role=get_user_model().Role.NEWHIRE,
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
        except Exception:
            # fail safe
            raise Http404

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(self.request, user)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        to_do = get_object_or_404(ToDo, pk=self.kwargs["pk"])
        to_do_user = get_object_or_404(ToDoUser, to_do=to_do, user=self.request.user)
        if len(to_do_user.completed_form_items) == len(to_do_user.form):
            context["form_already_filled"] = True

        context["object"] = to_do_user
        return context


@method_decorator(axes_dispatch, name="dispatch")
class PreboardingShortURLRedirectView(LoginRequiredMixin, RedirectView):
    pattern_name = "new_hire:preboarding"

    def dispatch(self, *args, **kwargs):
        try:
            user = User.objects.get(
                unique_url=self.request.GET.get("token", ""),
                start_day__gte=timezone.now(),
                role=get_user_model().Role.NEWHIRE,
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
        except Exception:
            # fail safe
            raise Http404

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(self.request, user)
        return super().dispatch(*args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        preboarding_user = PreboardingUser.objects.filter(
            user=self.request.user
        ).order_by("order")

        if not preboarding_user.exists():
            raise Http404

        return reverse("new_hire:preboarding", args=[preboarding_user.first().id])


class PreboardingDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_preboarding.html"
    model = PreboardingUser

    def dispatch(self, *args, **kwargs):
        # Make sure user is authenticated to view this object
        if self.request.user.is_authenticated:
            get_object_or_404(PreboardingUser, user=self.request.user, id=kwargs["pk"])
        # If user is not authenticated, then the default LoginRequiredMixin will catch
        # it
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
            button_text = _("Next")
        else:
            button_text = _("Restart")
            next_id = preboarding_user_items[0]

        context["button_text"] = button_text
        context["next_id"] = next_id
        context["amount_preboarding_pages"] = len(preboarding_user_items)
        return context


class ColleagueListView(LoginRequiredMixin, ListView):
    template_name = "new_hire_colleagues.html"
    model = User
    paginate_by = 20
    ordering = ["first_name", "last_name"]


class ColleagueSearchView(LoginRequiredMixin, ListView):
    """
    HTMX: Search for colleagues that fit search criteria.
    """

    template_name = "_new_hire_colleagues_search.html"
    model = get_user_model()

    def get_queryset(self):
        search = self.request.GET.get("search", "")
        if search == "":
            return get_user_model().objects.all()

        return get_user_model().objects.filter(
            first_name__icontains=search
        ) | get_user_model().objects.filter(last_name__icontains=search)


class ResourceListView(LoginRequiredMixin, ListView):
    template_name = "new_hire_resources.html"

    def get_queryset(self):
        return (
            ResourceUser.objects.filter(user=self.request.user)
            .order_by("resource__category")
            .select_related("resource__category")
            .prefetch_related("resource__chapters")
        )


class ResourceSearchView(LoginRequiredMixin, View):
    """
    HTMX: Search for resources that fit search criteria. Name and text.
    """

    def get(self, request, *args, **kwargs):
        results = Resource.objects.search(request.user, request.GET.get("search", ""))
        return render(request, "_new_hire_resources_search.html", {"results": results})


class ResourceDetailView(LoginRequiredMixin, DetailView):
    template_name = "new_hire_resource_detail.html"
    model = Resource

    def dispatch(self, *args, **kwargs):
        # Make sure it's either a course or if it's a course the user is not skipping
        # items
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
        # If chapter is a questions type, then add form if not filled in yet
        if (
            context["chapter"].type == Chapter.Type.QUESTIONS
            and not context["resource_user"]
            .answers.filter(chapter=context["chapter"])
            .exists()
        ):
            context["form"] = QuestionsForm(items=context["chapter"].content["blocks"])
        return context


class CourseNextStepView(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        resource_user = get_object_or_404(ResourceUser, pk=pk, user=request.user)
        chapter = resource_user.add_step()

        if chapter is None:
            messages.success(request, _("You have completed this course!"))
            Notification.objects.create(
                notification_type=Notification.Type.COMPLETED_COURSE,
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
        Adding chapter form arguments for creating/validation
        """
        resource_user = get_object_or_404(
            ResourceUser,
            user=self.request.user,
            resource=get_object_or_404(Resource, id=self.kwargs.get("pk", -1)),
        )
        chapter = get_object_or_404(Chapter, id=self.kwargs.get("chapter", -1))
        # return early if user should have access to this
        if chapter.order >= resource_user.step + 1:
            raise Http404

        if form_class is None:
            form_class = self.get_form_class()
        return form_class(items=chapter.content["blocks"], **self.get_form_kwargs())

    def form_valid(self, form):
        import os
        import uuid
        from django.conf import settings
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile

        resource_user = get_object_or_404(
            ResourceUser, resource__pk=self.kwargs.get("pk", -1), user=self.request.user
        )
        chapter = get_object_or_404(Chapter, id=self.kwargs.get("chapter", -1))

        # Process the form data
        processed_answers = {}

        for field_name, value in form.cleaned_data.items():
            # Get the question index from the field name (format: "item-{idx}")
            idx = int(field_name.split('-')[1])
            question = chapter.content["blocks"][idx]
            question_type = question.get('question_type', 'multiple_choice')

            if question_type in ['file_upload', 'photo_upload'] and value:
                # Handle file uploads
                file_obj = value
                original_name = file_obj.name

                # Generate a unique filename
                ext = os.path.splitext(original_name)[1]
                unique_filename = f"{uuid.uuid4()}{ext}"

                # Define the path where the file will be stored
                relative_path = f"course_answers/{resource_user.user.id}/{chapter.id}/{unique_filename}"

                # Save the file
                path = default_storage.save(relative_path, ContentFile(file_obj.read()))

                # Store file information in the answer
                processed_answers[field_name] = {
                    'type': question_type,
                    'filename': original_name,
                    'path': path,
                    'url': default_storage.url(path)
                }
            else:
                # For other question types, just store the value
                processed_answers[field_name] = value

        # Create a course answer object from the answers and then add it to the
        # resource user item
        course_answers = CourseAnswer.objects.create(
            chapter=chapter, answers=processed_answers
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
