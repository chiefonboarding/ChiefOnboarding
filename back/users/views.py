import uuid
from datetime import datetime

import pyotp
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.translation import ugettext as _
from django_q.tasks import async_task
from rest_framework import status, viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from twilio.rest import Client

from admin.appointments.serializers import AppointmentSerializer
from admin.integrations.google import Google
from admin.integrations.models import ScheduledAccess
from admin.integrations.slack import Error, PaidOnlyError, Slack
from admin.introductions.serializers import IntroductionSerializer
from admin.notes.models import Note
from admin.notes.serializers import NoteSerializer
from admin.preboarding.models import Preboarding
from admin.resources.models import Resource
from admin.resources.serializers import ResourceSlimSerializer
from admin.sequences.models import Condition, Sequence
from admin.sequences.serializers import ConditionSerializer
from admin.sequences.utils import get_task_items
from admin.to_do.serializers import ToDoFormSerializer
from new_hire.serializers import (
    NewHireResourceItemSerializer,
    PreboardingUserSerializer,
    ToDoUserSerializer,
)
from organization.models import Organization, WelcomeMessage
from slack_bot.slack import Slack as SlackBot

from .emails import (
    email_new_admin_cred,
    email_reopen_task,
    send_new_hire_cred,
    send_new_hire_preboarding,
    send_reminder_email,
)
from .models import NewHireWelcomeMessage, PreboardingUser, ResourceUser, ToDoUser
from .permissions import ManagerPermission
from .serializers import (
    AdminSerializer,
    EmployeeSerializer,
    NewHireProgressResourceSerializer,
    NewHireSerializer,
    NewHireWelcomeMessageSerializer,
    OTPRecoveryKeySerializer,
    UserLanguageSerializer,
)


class NewHireViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows new hires to be viewed, changed, edited or deleted.
    """

    serializer_class = NewHireSerializer
    permission_classes = [ManagerPermission]


    @action(detail=True, methods=["post"])
    def send_login_email(self, request, pk=None):
        user = self.get_object()
        translation.activate(user.language)
        message = WelcomeMessage.objects.get(language=user.language, message_type=1).message
        send_new_hire_cred(user, message)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def send_preboarding_details(self, request, pk=None):
        user = self.get_object()
        translation.activate(user.language)
        if request.data["type"] == "email":
            message = WelcomeMessage.objects.get(
                language=user.language, message_type=0
            ).message
            send_new_hire_preboarding(user, message)
        else:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=user.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=user.personalize(
                    WelcomeMessage.objects.get(language=user.language, message_type=2).message
                ),
            )
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        user = self.get_object()
        todo_serializer = ToDoUserSerializer(ToDoUser.objects.filter(user=user), many=True)
        resource_serializer = NewHireProgressResourceSerializer(
            ResourceUser.objects.filter(user=user), many=True
        )
        data = {"to_do": todo_serializer.data, "resources": resource_serializer.data}
        return Response(data)


    @action(detail=True, methods=["post"])
    def add_sequence(self, request, pk=None):
        user = self.get_object()
        Sequence.objects.get(id=request.data["id"]).assign_to_user(user)
        return Response()

    @action(detail=True, methods=["post"])
    def check_past_sequence(self, request, pk=None):
        user = self.get_object()
        items = []
        amount_days = user.workday()
        amount_days_before = user.days_before_starting()
        sequence_ids = request.data["sequence_ids"]
        for i in sequence_ids:
            seq = Sequence.objects.get(id=i)
            items.extend(
                ConditionSerializer(
                    seq.conditions.filter(condition_type=0, days__lte=amount_days),
                    many=True,
                ).data
            )
            items.extend(
                ConditionSerializer(
                    seq.conditions.filter(condition_type=2, days__gte=amount_days_before),
                    many=True,
                ).data
            )
        return Response(items)

    @action(detail=True, methods=["post"])
    def trigger_conditions(self, request, pk=None):
        user = self.get_object()
        for i in request.data["condition_ids"]:
            Condition.objects.get(id=i).process_condition(user)
        return Response()

    @action(detail=True, methods=["post"])
    def change_preboarding_order(self, request, pk=None):
        user = self.get_object()
        for idx, i in enumerate(request.data):
            pre = Preboarding.objects.get(id=i["id"])
            pre_user = PreboardingUser.objects.get(preboarding=pre, user=user)
            pre_user.order = idx
            pre_user.save()
        return Response()

    @action(detail=True, methods=["post", "put"])
    def access(self, request, pk=None):
        new_hire = self.get_object()
        if request.method == "PUT":
            ScheduledAccess.objects.create(
                new_hire=new_hire,
                integration=request.data["integration"],
                email=request.data["email"],
            )
            return Response({"status": "pending"})
        s = SlackBot() if request.data["integration"] == 1 else Google()
        if s.find_by_email(new_hire.email):
            return Response({"status": "exists"})
        items = ScheduledAccess.objects.filter(
            new_hire=new_hire, integration=request.data["integration"]
        ).exclude(status=1)
        if items.exists():
            return Response({"status": "pending"})
        return Response({"status": "not_found"})

    @action(detail=True, methods=["put"])
    def revoke_access(self, request, pk=None):
        new_hire = self.get_object()
        ScheduledAccess.objects.filter(
            new_hire=new_hire, integration=request.data["integration"]
        ).delete()
        if request.data["integration"] == 1:
            s = Slack()
            try:
                s.delete_user(new_hire.email)
            except PaidOnlyError:
                return Response({"error": "paid"}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({"error": "error"}, status=status.HTTP_400_BAD_REQUEST)
        if request.data["integration"] == 2:
            # g = Google()
            # g.delete_user(new_hire.email)
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or created.
    """

    serializer_class = EmployeeSerializer
    queryset = get_user_model().objects.all().order_by("id")

    @action(detail=True, methods=["post"])
    def give_slack_access(self, request, pk):
        user = self.get_object()
        s = SlackBot()
        response = s.find_by_email(user.email)
        if response:
            user.slack_user_id = response["user"]["id"]
            user.save()
            translation.activate(user.language)
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": _(
                            "Click on the button to see all the categories that are available to you!"
                        ),
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": _("resources")},
                            "style": "primary",
                            "value": "show:resources",
                        }
                    ],
                },
            ]
            s.set_user(user)
            res = s.send_message(blocks=blocks)
            user.slack_channel_id = res["channel"]
            user.save()
            return Response()
        return Response(
            {"error": _("We couldn't find anyone in Slack with the same email address.")},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["delete"])
    def revoke_slack_access(self, request, pk):
        user = self.get_object()
        user.slack_channel_id = None
        user.slack_user_id = None
        user.save()
        return Response()

    @action(detail=False, methods=["post"])
    def sync_google(self, request):
        g = Google()
        users = g.get_all_users()
        if users is not False:
            for i in users:
                get_user_model().objects.create(
                    email=i["primaryEmail"],
                    defaults={
                        "first_name": i["name"]["givenName"],
                        "last_name": i["name"]["familyName"],
                    },
                )
        return Response()

    @action(detail=False, methods=["post"])
    def sync_slack(self, request):
        s = SlackBot()
        users = s.get_all_users()
        for i in users:
            if i["id"] != "USLACKBOT" and not i["is_bot"] and "real_name" in i["profile"]:
                if len(i["profile"]["real_name"].split()) > 1:
                    first_name = i["profile"]["real_name"].split()[0]
                    last_name = i["profile"]["real_name"].split()[1]
                else:
                    first_name = i["profile"]["real_name"]
                    last_name = ""
                get_user_model().objects.get_or_create(
                    email=i["profile"]["email"],
                    defaults={
                        "position": i["profile"]["title"],
                        "phone": i["profile"]["phone"],
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                )
        return Response()

    @action(detail=True, methods=["get"])
    def get_resources(self, request, pk):
        books = ResourceSlimSerializer(self.get_object().resources, many=True)
        return Response(books.data)

    @action(detail=False, methods=["get"])
    def departments(self, request):
        departments = (
            get_user_model()
            .objects.all()
            .distinct("department")
            .exclude(department="")
            .values_list("department")
        )
        return Response(departments)

    @action(detail=True, methods=["post"])
    def add_resource(self, request, pk):
        user = self.get_object()
        if "resource" in self.request.data:
            book = get_object_or_404(Resource, id=self.request.data["resource"])
            user.resources.add(book)
        if "sequence" in self.request.data:
            seq = get_object_or_404(Sequence, id=request.data["sequence"])
            for i in seq.resources.all():
                user.resources.add(i)
        return Response(ResourceSlimSerializer(self.get_object().resources, many=True).data)

    @action(detail=True, methods=["put"])
    def delete_resource(self, request, pk):
        user = self.get_object()
        book = get_object_or_404(Resource, id=self.request.data["resource"])
        user.resources.remove(book)
        return Response(ResourceSlimSerializer(self.get_object().resources, many=True).data)

    @action(detail=True, methods=["post"])
    def send_employee_email(self, request, pk):
        user = self.get_object()
        password = uuid.uuid4().hex[:12].upper()
        user.set_password(password)
        user.save()
        email_new_admin_cred(user, password)
        return Response()


# these two views should be made DRY


class ToDoUserView(APIView):
    """
    API endpoint that allows you to remind a new hire of a to do or reopen it.
    """

    def post(self, request, id):
        # reminding someone
        t_u = ToDoUser.objects.get(id=id)
        t_u.reminded = datetime.now()
        t_u.save()
        if t_u.user.slack_user_id:
            s = SlackBot()
            s.set_user(t_u.user)
            blocks = s.format_to_do_block(
                pre_message=_("Don't forget this to do item!"), items=[t_u]
            )
            s.send_message(blocks=blocks)
        else:
            send_reminder_email(t_u)
        return Response()

    def put(self, request, id):
        # reopen task
        t_u = ToDoUser.objects.get(id=id)
        t_u.completed = False
        t_u.form = []
        t_u.save()
        if t_u.user.slack_user_id:
            s = SlackBot()
            s.set_user(t_u.user)
            blocks = s.format_to_do_block(
                pre_message=_("This task has just been reopened! " + request.data["message"]),
                items=[t_u],
            )
            s.send_message(blocks=blocks)
        else:
            email_reopen_task(t_u, request.data["message"], t_u.user)
        return Response()


class ResourceUserView(APIView):
    """
    API endpoint that allows you to remind a new hire of a to do or reopen it.
    """

    def post(self, request, id):
        # reminding someone
        t_u = ResourceUser.objects.get(id=id)
        t_u.reminded = datetime.now()
        t_u.save()
        if t_u.user.slack_user_id:
            s = SlackBot()
            s.set_user(t_u.user)
            blocks = s.format_resource_block(
                pre_message=_("Don't forget this to do item!"), items=[t_u]
            )
            s.send_message(blocks=blocks)
        else:
            send_reminder_email(t_u)
        return Response()

    def put(self, request, id):
        # reopen task
        t_u = ResourceUser.objects.get(id=id)
        t_u.completed_course = False
        t_u.answers.clear()
        t_u.save()
        if t_u.user.slack_user_id:
            s = SlackBot()
            s.set_user(t_u.user)
            blocks = s.format_resource_block(
                pre_message=_("This task has just been reopened! " + request.data["message"]),
                items=[t_u],
            )
            s.send_message(blocks=blocks)
        else:
            email_reopen_task(t_u, request.data["message"], t_u.user)
        return Response()
