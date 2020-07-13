from django.conf import settings
from django.contrib.auth import login, get_user_model
from django.shortcuts import get_object_or_404
from django.utils import translation
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle

from users.serializers import NewHireSerializer, EmployeeSerializer
from organization.serializers import BaseOrganizationSerializer
from organization.models import Organization
from users.permissions import NewHirePermission
from users.models import User, ToDoUser, PreboardingUser, ResourceUser
from introductions.serializers import IntroductionSerializer

from new_hire.serializers import ToDoUserSerializer, NewHireResourceSerializer, PreboardingUserSerializer, NewHireBadgeSerializer, NewHireResourceItemSerializer

from resources.serializers import ResourceSerializer
from resources.models import Chapter, CourseAnswer
from to_do.serializers import ToDoSerializer
from to_do.models import ToDo
from badges.serializers import BadgeSerializer

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
        response = Response({'new_hire': user_serializer.data, 'org': org_serializer.data})
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, request.user.language)
        return response


class AuthenticateView(APIView):
    """
    API endpoint that allows colleagues to be viewed.
    """
    permission_classes = (AllowAny,)
    throttle_classes = [AnonRateThrottle,]

    def post(self, request):
        user = get_object_or_404(get_user_model(), unique_url=request.data['token'])
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

        if resource_user.step < int(request.data['step']):
            resource_user.step = int(request.data['step'])
            resource_user.save()
        return Response()


class CourseItemView(APIView):
    """
    API endpoint that allows a resource item to be viewed.
    """
    permission_classes = (NewHirePermission,)

    def get(self, request, id):
        b_u = ResourceUser.objects.filter(resource=request.user.resources.get(id=id)).first()
        resources = NewHireResourceItemSerializer(b_u, context={'request': request})
        return Response(resources.data)

    def post(self, request, id):
        b_u = ResourceUser.objects.get(id=id)
        resource = Resource.objects.get(id=request.data['id'])
        c_a = CourseAnswer.objects.create(resource=resource, answers=request.data['answers'])
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
        to_do.form = request.data['data']
        to_do.save()
        data = to_do.mark_completed()
        data['to_do'] = ToDoSerializer(data['to_do'], many=True).data
        data['resources'] = ResourceSerializer(data['resources'], many=True).data
        data['badges'] = BadgeSerializer(data['badges'], many=True).data
        return Response(data)


class ToDoPreboardingView(APIView):
    """
    API endpoint that allows to do items to be viewed.
    """
    permission_classes = (NewHirePermission,)

    def post(self, request, id):
        to_do = get_object_or_404(ToDo, id=id)
        to_do_user = request.user.preboarding.filter(to_do=to_do, user=request.user)
        to_do_user.form = request.data['data']
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
        to_do.form = request.data['data']
        to_do.save()
        return Response()


class PreboardingView(APIView):
    """
    API endpoint that allows preboarding items to be viewed.
    """
    permission_classes = (NewHirePermission,)

    def get(self, request):
        preboarding_items = PreboardingUserSerializer(PreboardingUser.objects.filter(user=request.user), many=True)
        return Response(preboarding_items.data)

    def post(self, request):
        pre = get_object_or_404(PreboardingUser, user=request.user, id=request.data['id'])
        pre.form = request.data['form']
        pre.completed = True
        pre.save()
        return Response()


class BadgeView(APIView):
    """
    API endpoint that allows badges items to be viewed.
    """
    permission_classes = (NewHirePermission,)

    def get(self, request):
        badges = NewHireBadgeSerializer(request.user.badges, many=True)
        return Response(badges.data)

