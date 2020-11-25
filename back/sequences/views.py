from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Sequence, ExternalMessage, Condition, PendingAdminTask
from .serializers import SequenceSerializer, ExternalMessageSerializer, SequenceListSerializer, \
    PendingAdminTaskSerializer
from to_do.models import ToDo

from django.apps import apps
from .emails import send_sequence_message
from slack_bot.slack import Slack



class SequenceViewSet(viewsets.ModelViewSet):
    serializer_class = SequenceSerializer
    queryset = Sequence.objects.all().order_by('id')

    def get_serializer_class(self):
        if self.action == 'list':
            return SequenceListSerializer
        return SequenceSerializer

    def _get_condition_items(self, c):
        return [
            {'app': 'to_do', 'model': 'ToDo', 'item': 'to_do', 'c_model': c.to_do},
            {'app': 'resources', 'model': 'Resource', 'item': 'resources', 'c_model': c.resources},
            {'app': 'sequences', 'model': 'PendingAdminTask', 'item': 'admin_tasks', 'c_model': c.admin_tasks},
            {'app': 'badges', 'model': 'Badge', 'item': 'badges', 'c_model': c.badges},
            {'app': 'sequences', 'model': 'ExternalMessage', 'item': 'external_messages', 'c_model': c.external_messages},
            {'app': 'introductions', 'model': 'Introduction', 'item': 'introductions', 'c_model': c.introductions}
        ]

    def _save_sequence(self, data, sequence=None):
        print(data)

        # saving collection part
        items = [
            {'app': 'to_do', 'model': 'ToDo', 'item': 'to_do', 's_model': sequence.to_do},
            {'app': 'resources', 'model': 'Resource', 'item': 'resources', 's_model': sequence.resources},
            {'app': 'preboarding', 'model': 'Preboarding', 'item': 'preboarding', 's_model': sequence.preboarding}
        ]
        for j in items:
            for i in data['collection'][j['item']]:
                item = apps.get_model(app_label=j['app'], model_name=j['model']).objects.get(id=i['id'])
                j['s_model'].add(item)

        # save sequence part
        for item in data['conditions']:
            c = Condition.objects.create(condition_type=item['condition_type'], days=item['days'], sequence=sequence)
            if len(item['condition_to_do']):
                c.condition_to_do.set([ToDo.objects.get(id=i['id']) for i in item['condition_to_do']])

            items = self._get_condition_items(c)
            for j in items:
                for i in item[j['item']]:
                    new_item = apps.get_model(app_label=j['app'], model_name=j['model']).objects.get(id=i['id'])
                    j['c_model'].add(new_item)

        return False

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sequence = Sequence.objects.create(name=serializer.validated_data['name'])
        data = self._save_sequence(request.data, sequence)
        if data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data={'name': request.data['name']}, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        Condition.objects.filter(sequence=instance).delete()
        instance.to_do.clear()
        instance.resources.clear()
        instance.preboarding.clear()
        instance.appointments.clear()
        data = self._save_sequence(request.data, instance)
        if data:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_200_OK)


class SaveExternalMessage(APIView):
    def post(self, request):
        if 'id' in request.data:
            ext_message = ExternalMessage.objects.get(id=request.data['id'])
            external_message = ExternalMessageSerializer(ext_message, data=request.data)
        else:
            external_message = ExternalMessageSerializer(data=request.data)
        external_message.is_valid(raise_exception=True)
        external_message.save()
        return Response(external_message.data)


class SendTestMessage(APIView):
    def post(self, request, id):
        ext_message = ExternalMessage.objects.get(id=id)
        if ext_message.send_via == 0:  # email
            send_sequence_message(request.user, ext_message.email_message())
        elif ext_message.send_via == 1:  # slack
            s = Slack()
            s.set_user(request.user)
            blocks = []
            for j in ext_message.content_json.all():
                blocks.append(j.to_slack_block(request.user))
            s.send_message(blocks=blocks)
        return Response()


class SaveAdminTask(APIView):
    def post(self, request):
        if 'id' in request.data:
            pending_admin_task = PendingAdminTask.objects.get(id=request.data['id'])
            pending_task = PendingAdminTaskSerializer(pending_admin_task, data=request.data, partial=True)
        else:
            pending_task = PendingAdminTaskSerializer(data=request.data)
        pending_task.is_valid(raise_exception=True)
        pending_task.save()
        return Response(pending_task.data)
