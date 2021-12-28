from datetime import datetime, timedelta

from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth import get_user_model, login, signals
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from admin.badges.serializers import BadgeSerializer
from admin.introductions.serializers import IntroductionSerializer
from admin.resources.models import Chapter, CourseAnswer, Resource
from admin.resources.serializers import ResourceSerializer
from admin.to_do.models import ToDo
from admin.to_do.serializers import ToDoSerializer
from new_hire.serializers import (NewHireBadgeSerializer,
                                  NewHireResourceItemSerializer,
                                  NewHireResourceSerializer,
                                  PreboardingUserSerializer,
                                  ToDoUserSerializer)
from organization.models import Organization
from organization.serializers import BaseOrganizationSerializer
from users.models import (NewHireWelcomeMessage, PreboardingUser, ResourceUser,
                          ToDoUser, User)
from users.permissions import NewHirePermission
from users.serializers import EmployeeSerializer, NewHireSerializer


class NewHireDashboard(TemplateView):
    template_name = "new_hire_to_dos.html"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        new_hire = self.request.user
        context = super().get_context_data(**kwargs)

        context["overdue_to_do_items"] = ToDoUser.objects.filter(
            user=new_hire, to_do__due_on_day__lt=new_hire.workday(), completed=False
        )

        to_do_items = ToDoUser.objects.filter(user=new_hire, to_do__due_on_day__gte=new_hire.workday())

        # Group items by amount work days
        items_by_date = []
        for to_do_user in to_do_items:
            # Check if to do is already in any of the new items_by_date
            to_do = to_do_user.to_do
            if not any([item for item in items_by_date if item["day"] == to_do.due_on_day]):
                new_date = {
                    "day": to_do.due_on_day,
                    "items": [
                        to_do,
                    ],
                }
                items_by_date.append(new_date)
            else:
                # Can never be two or more, since it's catching it if it already exists
                existing_date = [item for item in items_by_date if item["day"] == to_do.due_on_day][0]
                existing_date["items"].append(to_do_user)

        # Convert days to date object
        for obj in items_by_date:
            obj["date"] = self.request.user.start_day + timedelta(days=obj["day"] - 1)

        context["to_do_items"] = items_by_date

        context["title"] = "Things you need to do"
        context["subtitle"] = "Tasks"
        return context


class ToDoDetailView(DetailView):
    template_name = "new_hire_to_do.html"
    model = ToDoUser


@method_decorator(axes_dispatch, name="dispatch")
class PreboardingShortURLRedirectView(RedirectView):
    pattern_name = "new_hire:preboarding"

    def dispatch(self, *args, **kwargs):
        try:
            user = User.objects.get(unique_url=self.request.GET.get("token", ""), start_day__gte=timezone.now(), role=0)
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
        preboarding_user = PreboardingUser.objects.filter(user=self.request.user).order_by("order")
        return reverse("new_hire:preboarding", args=[preboarding_user.first().id])


class PreboardingDetailView(DetailView):
    template_name = "new_hire_preboarding.html"
    model = PreboardingUser

    def dispatch(self, *args, **kwargs):
        # Make sure user is authenticated to view this object
        get_object_or_404(PreboardingUser, user=self.request.user, id=kwargs["pk"])
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        preboarding_user_items = list(
            PreboardingUser.objects.filter(user=self.request.user).order_by("order").values_list("id", flat=True)
        )
        index_current_item = preboarding_user_items.index(self.object.id)

        # Add new hire welcome messages to first page
        if index_current_item == 0 and NewHireWelcomeMessage.objects.filter(new_hire=self.request.user).exists():
            context["welcome_messages"] = NewHireWelcomeMessage.objects.filter(new_hire=self.request.user)

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


class ColleagueListView(ListView):
    template_name = "new_hire_colleagues.html"
    model = User
    paginate_by = 20


class ColleagueSearchView(ListView):
    template_name = "_new_hire_colleagues_search.html"
    model = User

    def get_queryset(self):
        search = self.request.GET.get("search", "")
        return get_user_model().objects.filter(Q(first_name__icontains=search), Q(last_name__icontains=search))


class ResourceListView(TemplateView):
    template_name = "new_hire_resources.html"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # resources = ResourceUser.objects.filter(user=request.user)

        return context


class ToDoCompleteView(RedirectView):
    pattern_name = "new_hire:to_do"

    def get_redirect_url(self, *args, **kwargs):
        to_do_user = get_object_or_404(ToDoUser, pk=kwargs["pk"], user=self.request.user)
        to_do_user.completed = True
        to_do_user.save()
        return super().get_redirect_url(*args, **kwargs)


class MeView(APIView):
    """
    API endpoint that allows employees to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        user_serializer = NewHireSerializer(request.user)
        org_serializer = BaseOrganizationSerializer(Organization.object.get())
        translation.activate(request.user.language)
        request.session[translation.LANGUAGE_SESSION_KEY] = request.user.language
        response = Response({"new_hire": user_serializer.data, "org": org_serializer.data})
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, request.user.language)
        return response


class AuthenticateView(APIView):
    """
    API endpoint that allows colleagues to be viewed.
    """

    permission_classes = (AllowAny,)
    throttle_classes = [
        AnonRateThrottle,
    ]

    def post(self, request):
        user = get_object_or_404(get_user_model(), unique_url=request.data['token'], role=0)
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return Response()


class ColleagueView(APIView):
    """
    API endpoint that allows colleagues to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        colleagues = EmployeeSerializer(get_user_model().objects.all(), many=True)
        return Response(colleagues.data)


class IntroductionView(APIView):
    """
    API endpoint that allows introductions to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        colleagues = IntroductionSerializer(request.user.introductions, many=True)
        return Response(colleagues.data)


class ResourceView(APIView):
    """
    API endpoint that allows resources to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        resources = NewHireResourceSerializer(request.user.resources, many=True)
        return Response(resources.data)


class ResourceItemView(APIView):
    """
    API endpoint that allows a resource item to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request, id):
        resources = ResourceSerializer(request.user.resources.get(id=id))
        return Response(resources.data)


class CourseStep(APIView):
    """
    API endpoint that allows a resource item to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def post(self, request, id):
        resource_user = get_object_or_404(ResourceUser, id=id)

        if resource_user.step < int(request.data["step"]):
            resource_user.step = int(request.data["step"])
            resource_user.save()
        return Response()


class CourseItemView(APIView):
    """
    API endpoint that allows a resource item to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request, id):
        b_u = ResourceUser.objects.filter(resource=request.user.resources.get(id=id)).first()
        resources = NewHireResourceItemSerializer(b_u, context={"request": request})
        return Response(resources.data)

    def post(self, request, id):
        b_u = ResourceUser.objects.get(id=id)
        resource = Resource.objects.get(id=request.data["id"])
        c_a = CourseAnswer.objects.create(resource=resource, answers=request.data["answers"])
        b_u.answers.add(c_a)
        return Response()


class ToDoView(APIView):
    """
    API endpoint that allows to do items to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        to_do_items = ToDoUserSerializer(ToDoUser.objects.filter(user=request.user), many=True)
        return Response(to_do_items.data)

    def post(self, request, id):
        to_do = get_object_or_404(ToDoUser, user=request.user, id=id)
        to_do.form = request.data["data"]
        to_do.save()
        data = to_do.mark_completed()
        data["to_do"] = ToDoSerializer(data["to_do"], many=True).data
        data["resources"] = ResourceSerializer(data["resources"], many=True).data
        data["badges"] = BadgeSerializer(data["badges"], many=True).data
        return Response(data)


class ToDoPreboardingView(APIView):
    """
    API endpoint that allows to do items to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def post(self, request, id):
        to_do = get_object_or_404(ToDo, id=id)
        to_do_user = request.user.preboarding.filter(to_do=to_do, user=request.user)
        to_do_user.form = request.data["data"]
        to_do_user.save()
        return Response(data)


class ToDoSlackView(APIView):
    """
    API endpoint that allows to do items to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request, id):
        to_do_items = ToDoUserSerializer(ToDoUser.objects.get(user=request.user, id=id))
        return Response(to_do_items.data)

    def post(self, request, id):
        to_do = get_object_or_404(ToDoUser, user=request.user, id=id)
        to_do.form = request.data["data"]
        to_do.save()
        return Response()


# class PreboardingView(APIView):
#     """
#     API endpoint that allows preboarding items to be viewed.
#     """
#
#     permission_classes = (NewHirePermission,)
#
#     def get(self, request):
#         preboarding_items = PreboardingUserSerializer(
#             PreboardingUser.objects.filter(user=request.user).order_by("order"),
#             many=True,
#         )
#         return Response(preboarding_items.data)
#
#     def post(self, request):
#         pre = get_object_or_404(PreboardingUser, user=request.user, id=request.data["id"])
#         pre.form = request.data["form"]
#         pre.completed = True
#         pre.save()
#         return Response()


class BadgeView(APIView):
    """
    API endpoint that allows badges items to be viewed.
    """

    permission_classes = (NewHirePermission,)

    def get(self, request):
        badges = NewHireBadgeSerializer(request.user.badges, many=True)
        return Response(badges.data)
