from datetime import datetime
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.translation import ugettext as _
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.views import APIView
from twilio.rest import Client

from .emails import send_reminder_email, send_new_hire_cred, email_new_admin_cred, send_new_hire_preboarding, \
    email_reopen_task
from .models import ToDoUser, PreboardingUser, ResourceUser, NewHireWelcomeMessage
from .tasks import send_new_hire_credentials
from .serializers import NewHireSerializer, AdminSerializer, EmployeeSerializer, \
    UserLanguageSerializer, NewHireProgressResourceSerializer, \
    NewHireWelcomeMessageSerializer
from .permissions import ManagerPermission
from notes.serializers import NoteSerializer
from notes.models import Note
from to_do.serializers import ToDoFormSerializer
from new_hire.serializers import ToDoUserSerializer, NewHireResourceItemSerializer, PreboardingUserSerializer
from resources.serializers import ResourceSlimSerializer
from introductions.serializers import IntroductionSerializer
from appointments.serializers import AppointmentSerializer
from sequences.serializers import ConditionSerializer
from sequences.models import Condition, Sequence
from resources.models import Resource
from preboarding.models import Preboarding
from slack_bot.slack import Slack as SlackBot
from integrations.slack import Slack, PaidOnlyError, Error
from integrations.models import ScheduledAccess
from sequences.utils import get_task_items
from organization.models import WelcomeMessage
from integrations.google import Google
from django.db.models import Prefetch
import pyotp

class NewHireViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows new hires to be viewed, changed, edited or deleted.
    """
    serializer_class = NewHireSerializer
    permission_classes = [ManagerPermission]

    def get_queryset(self):
        # if user is not admin, then only show records relevant to the manager
        all_new_hires = get_user_model().new_hires.select_related('profile_image', 'buddy', 'manager').prefetch_related('resources', 'to_do', 'introductions', 'preboarding', 'badges',
                Prefetch('conditions', queryset=Condition.objects.prefetch_related('condition_to_do', 'to_do', 'badges', 'resources', 'admin_tasks', 'external_messages', 'introductions'))).all()
        if self.request.user.role == 1:
            return all_new_hires 
        return all_new_hires.filter(manager=self.request.user)

    def create(self, request, *args, **kwargs):
        sequences = request.data.pop('sequences')
        google = request.data.pop('google')
        slack = request.data.pop('slack')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_hire = serializer.save()
        for i in sequences:
            Sequence.objects.get(id=i['id']).assign_to_user(new_hire)
        if slack['create']:
            ScheduledAccess.objects.create(new_hire=new_hire, integration=1, status=0, email=slack['email'])
        if google['create']:
            ScheduledAccess.objects.create(new_hire=new_hire, integration=2, status=0, email=google['email'])
        new_hire_time = new_hire.get_local_time()
        if new_hire_time.date() >= new_hire.start_day and new_hire_time.hour >= 7 and new_hire_time.weekday() < 5:
            send_new_hire_credentials.apply_async([new_hire.id], countdown=3)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def send_login_email(self, request, pk=None):
        user = self.get_object()
        translation.activate(user.language)
        message = WelcomeMessage.objects.get(language=user.language, message_type=1).message
        send_new_hire_cred(user, message)
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def send_preboarding_details(self, request, pk=None):
        user = self.get_object()
        translation.activate(user.language)
        if request.data['type'] == 'email':
            message = WelcomeMessage.objects.get(language=user.language, message_type=0).message
            send_new_hire_preboarding(user, message)
        else:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=user.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=user.personalize(WelcomeMessage.objects.get(language=user.language, message_type=2).message))
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def notes(self, request, pk=None):
        if request.method == 'POST':
            serializer = NoteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(new_hire=self.get_object(), admin=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        notes = Note.objects.filter(new_hire=self.get_object()).order_by('-created')
        return Response(NoteSerializer(notes, many=True).data)

    @action(detail=True, methods=['get'])
    def forms(self, request, pk=None):
        serializer = ToDoFormSerializer(ToDoUser.objects.filter(user=self.get_object(), completed=True),
                                        many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        todo_serializer = ToDoUserSerializer(ToDoUser.objects.filter(user=self.get_object()), many=True)
        resource_serializer = NewHireProgressResourceSerializer(ResourceUser.objects.filter(user=self.get_object()),
                                                                many=True)
        data = {'to_do': todo_serializer.data, 'resources': resource_serializer.data}
        return Response(data)

    @action(detail=True, methods=['get'])
    def welcome_messages(self, request, pk=None):
        serializer = NewHireWelcomeMessageSerializer(NewHireWelcomeMessage.objects.filter(new_hire=self.get_object()),
                                                     many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post', 'put'])
    def tasks(self, request, pk=None):
        if request.method == 'POST' or request.method == 'PUT':
            items = get_task_items(self.get_object())
            for i in items:
                if i['item'] == request.data['type']:
                    item = apps.get_model(
                        app_label=i['app'],
                        model_name=i['model']).objects.get(id=request.data['item']['id'])
                    i['s_model'].add(item) if request.method == 'POST' else i['s_model'].remove(item)
                    break
            return Response(request.data['item'], status=status.HTTP_201_CREATED)
        return Response({
            'preboarding': PreboardingUserSerializer(PreboardingUser.objects.filter(user=self.get_object()),
                                                     many=True).data,
            'to_do': ToDoUserSerializer(ToDoUser.objects.filter(user=self.get_object()), many=True).data,
            'resources': NewHireResourceItemSerializer(ResourceUser.objects.filter(user=self.get_object()),
                                                       many=True).data,
            'introductions': IntroductionSerializer(self.get_object().introductions, many=True).data,
            'appointments': AppointmentSerializer(self.get_object().appointments, many=True).data,
            'conditions': ConditionSerializer(self.get_object().conditions, many=True).data
        })

    @action(detail=True, methods=['post'])
    def add_sequence(self, request, pk=None):
        user = self.get_object()
        Sequence.objects.get(id=request.data['id']).assign_to_user(user)
        return Response()

    @action(detail=True, methods=['post'])
    def check_past_sequence(self, request, pk=None):
        user = self.get_object()
        items = []
        amount_days = user.workday()
        amount_days_before = user.days_before_starting()
        sequence_ids = request.data['sequence_ids']
        for i in sequence_ids:
            seq = Sequence.objects.get(id=i)
            items.extend(
                ConditionSerializer(seq.conditions.filter(condition_type=0, days__lte=amount_days), many=True).data)
            items.extend(ConditionSerializer(seq.conditions.filter(condition_type=2, days__gte=amount_days_before),
                                             many=True).data)
        return Response(items)

    @action(detail=True, methods=['post'])
    def trigger_conditions(self, request, pk=None):
        user = self.get_object()
        for i in request.data['condition_ids']:
            Condition.objects.get(id=i).process_condition(user)
        return Response()

    @action(detail=True, methods=['post'])
    def change_preboarding_order(self, request, pk=None):
        user = self.get_object()
        for idx, i in enumerate(request.data):
            pre = Preboarding.objects.get(id=i['id'])
            pre_user = PreboardingUser.objects.get(preboarding=pre, user=user)
            pre_user.order = idx
            pre_user.save()
        return Response()

    @action(detail=True, methods=['post', 'put'])
    def access(self, request, pk=None):
        new_hire = self.get_object()
        if request.method == 'PUT':
            ScheduledAccess.objects.create(
                new_hire=new_hire,
                integration=request.data['integration'],
                email=request.data['email']
            )
            return Response({'status': 'pending'})
        s = SlackBot() if request.data['integration'] == 1 else Google()
        if s.find_by_email(new_hire.email):
            return Response({'status': 'exists'})
        items = ScheduledAccess.objects.filter(new_hire=new_hire, integration=request.data['integration']).exclude(
            status=1)
        if items.exists():
            return Response({'status': 'pending'})
        return Response({'status': 'not_found'})

    @action(detail=True, methods=['put'])
    def revoke_access(self, request, pk=None):
        new_hire = self.get_object()
        ScheduledAccess.objects.filter(
            new_hire=new_hire,
            integration=request.data['integration']).delete()
        if request.data['integration'] == 1:
            s = Slack()
            try:
                s.delete_user(new_hire.email)
            except PaidOnlyError:
                return Response({'error': 'paid'}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': 'error'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data['integration'] == 2:
            g = Google()
            g.delete_user(new_hire.email)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminViewSet(viewsets.ModelViewSet):
    serializer_class = AdminSerializer
    queryset = get_user_model().admins.all()
    
    def get_permissions(self):
        if self.action == "list":
            self.permission_classes = [ManagerPermission]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = serializer.save()
        password = uuid.uuid4().hex[:12].upper()
        user.set_password(password)
        user.save()
        email_new_admin_cred(user, password)

    def delete(self, request):
        # preventing lockout
        if self.get_object() != request.user:
            self.get_object().delete()
        return Response()

    @action(detail=False, methods=['post'])
    def validate_totp(self, request):
        otp = request.data['otp'] if 'otp' in request.data else ''
        totp = pyotp.TOTP(request.user.totp_secret)
        is_valid = totp.verify(otp)
        if is_valid:
            request.user.requires_otp = True
            request.user.save()
            return Response({ 'recovery_key': request.user.otp_recovery_key })
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def get_totp_qr(self, request):
        otp_url = pyotp.totp.TOTP(request.user.totp_secret).provisioning_uri(name=request.user.email, issuer_name='ChiefOnboarding')
        return Response({ 'otp_url': otp_url })

    @action(detail=False, methods=['get'], permission_classes=[ManagerPermission])
    def me(self, request):
        admin = AdminSerializer(request.user)
        return Response(admin.data)

    @action(detail=False, methods=['post'], permission_classes=[ManagerPermission])
    def seen_updates(self, request):
        request.user.seen_updates = request.user.get_local_time().date()
        request.user.save()
        return Response(AdminSerializer(request.user).data)

    @action(detail=False, methods=['post'])
    def language(self, request):
        serializer = UserLanguageSerializer(request.user, request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employees to be viewed or created.
    """

    serializer_class = EmployeeSerializer
    queryset = get_user_model().objects.all().order_by('id')

    @action(detail=True, methods=['post'])
    def give_slack_access(self, request, pk):
        user = self.get_object()
        s = SlackBot()
        response = s.find_by_email(user.email)
        if response:
            user.slack_user_id = response['user']['id']
            user.save()
            translation.activate(user.language)
            blocks = [{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _("Click on the button to see all the categories that are available to you!")
                }
            },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": _("resources")
                            },
                            "style": "primary",
                            "value": "show:resources"
                        }
                    ]
                }
            ]
            s.set_user(user)
            res = s.send_message(blocks=blocks)
            user.slack_channel_id = res['channel']
            user.save()
            return Response()
        return Response({"error": _('We couldn\'t find anyone in Slack with the same email address.')},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def revoke_slack_access(self, request, pk):
        user = self.get_object()
        user.slack_channel_id = None
        user.slack_user_id = None
        user.save()
        return Response()

    @action(detail=False, methods=['post'])
    def sync_google(self, request):
        g = Google()
        users = g.get_all_users()
        if users is not False:
            for i in users:
                get_user_model().objects.create(
                    email=i['primaryEmail'],
                    defaults={
                        'first_name': i['name']['givenName'],
                        'last_name': i['name']['familyName']
                    }
                )
        return Response()

    @action(detail=False, methods=['post'])
    def sync_slack(self, request):
        s = SlackBot()
        users = s.get_all_users()
        for i in users:
            if i['id'] != 'USLACKBOT' and not i['is_bot'] and 'first_name' in i['profile']:
                get_user_model().objects.get_or_create(
                    email=i['profile']['email'],
                    defaults={
                        'position': i['profile']['title'],
                        'phone': i['profile']['phone'],
                        'first_name': i['profile']['first_name'],
                        'last_name': i['profile']['last_name']
                    }
                )
        return Response()

    @action(detail=True, methods=['get'])
    def get_resources(self, request, pk):
        books = ResourceSlimSerializer(self.get_object().resources, many=True)
        return Response(books.data)

    @action(detail=False, methods=['get'])
    def departments(self, request):
        departments = get_user_model().objects.all().distinct('department').exclude(department='').values_list('department')
        return Response(departments)

    @action(detail=True, methods=['post'])
    def add_resource(self, request, pk):
        user = self.get_object()
        if 'resource' in self.request.data:
            book = get_object_or_404(Resource, id=self.request.data['resource'])
            user.resources.add(book)
        if 'sequence' in self.request.data:
            seq = get_object_or_404(Sequence, id=request.data['sequence'])
            for i in seq.resources.all():
                user.resources.add(i)
        return Response(ResourceSlimSerializer(self.get_object().resources, many=True).data)

    @action(detail=True, methods=['put'])
    def delete_resource(self, request, pk):
        user = self.get_object()
        book = get_object_or_404(Resource, id=self.request.data['resource'])
        user.resources.remove(book)
        return Response(ResourceSlimSerializer(self.get_object().resources, many=True).data)

    @action(detail=True, methods=['post'])
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
            blocks = s.format_to_do_block(pre_message=_('Don\'t forget this to do item!'), items=[t_u])
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
            blocks = s.format_to_do_block(pre_message=_('This task has just been reopened! ' + request.data['message']),
                                          items=[t_u])
            s.send_message(blocks=blocks)
        else:
            email_reopen_task(t_u, request.data['message'], t_u.user)
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
            blocks = s.format_resource_block(pre_message=_('Don\'t forget this to do item!'), items=[t_u])
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
                pre_message=_('This task has just been reopened! ' + request.data['message']), items=[t_u])
            s.send_message(blocks=blocks)
        else:
            email_reopen_task(t_u, request.data['message'], t_u.user)
        return Response()
