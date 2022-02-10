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
from new_hire.serializers import (NewHireResourceItemSerializer,
                                  PreboardingUserSerializer,
                                  ToDoUserSerializer)
from organization.models import Organization, WelcomeMessage
from slack_bot.slack import Slack as SlackBot

from .emails import (email_new_admin_cred, email_reopen_task,
                     send_new_hire_cred, send_new_hire_preboarding,
                     send_reminder_email)
from .models import (NewHireWelcomeMessage, PreboardingUser, ResourceUser,
                     ToDoUser)
from .permissions import ManagerPermission
from .serializers import (AdminSerializer, EmployeeSerializer,
                          NewHireProgressResourceSerializer, NewHireSerializer,
                          NewHireWelcomeMessageSerializer,
                          OTPRecoveryKeySerializer, UserLanguageSerializer)


class NewHireViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows new hires to be viewed, changed, edited or deleted.
    """

    serializer_class = NewHireSerializer
    permission_classes = [ManagerPermission]

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
            return Response({"status": "pending"})
        s = SlackBot() if request.data["integration"] == 1 else Google()
        if s.find_by_email(new_hire.email):
            return Response({"status": "exists"})
        if items.exists():
            return Response({"status": "pending"})
        return Response({"status": "not_found"})

    @action(detail=True, methods=["put"])
    def revoke_access(self, request, pk=None):
        new_hire = self.get_object()
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
                pre_message=_(
                    "This task has just been reopened! " + request.data["message"]
                ),
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
                pre_message=_(
                    "This task has just been reopened! " + request.data["message"]
                ),
                items=[t_u],
            )
            s.send_message(blocks=blocks)
        else:
            email_reopen_task(t_u, request.data["message"], t_u.user)
        return Response()
