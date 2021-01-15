from django.conf import settings
from django.db import models

from preboarding.models import Preboarding
from resources.models import Resource
from to_do.models import ToDo
from introductions.models import Introduction
from appointments.models import Appointment
from introductions.models import Introduction

from badges.models import Badge
from admin_tasks.models import AdminTask

from admin_tasks.models import NOTIFICATION_CHOICES, PRIORITY_CHOICES

from sequences.utils import get_condition_items

from misc.models import Content
from twilio.rest import Client

from .emails import send_sequence_message
from slack_bot.slack import Slack


class Sequence(models.Model):
    name = models.CharField(max_length=240)
    preboarding = models.ManyToManyField(Preboarding)
    to_do = models.ManyToManyField(ToDo)
    resources = models.ManyToManyField(Resource)
    appointments = models.ManyToManyField(Appointment)
    auto_add = models.BooleanField(default=False)

    def assign_to_user(self, user):
        a = [
            {'u_model': user.to_do, 's_model': self.to_do},
            {'u_model': user.resources, 's_model': self.resources},
            {'u_model': user.preboarding, 's_model': self.preboarding},
        ]
        # check for every one if they are already there, if not -> adding it.
        for j in a:
            for x in j['s_model'].all():
                if not j['u_model'].filter(id=x.id).exists():
                    j['u_model'].add(x)

        # adding conditions
        for i in self.conditions.all():
            original_record = Condition.objects.get(id=i.id)
            # checking if this condition is already
            if original_record.condition_type == 0 or original_record.condition_type == 2:
                condition = user.conditions.filter(condition_type=original_record.condition_type, days=original_record.days).first()
            else:
                conditions = user.conditions.filter(condition_type=1)
                condition = None
                for j in conditions:
                    valid = True
                    if original_record.condition_to_do.count() is not j.condition_to_do.count():
                        continue
                    for h in original_record.condition_to_do.all():
                        print(j.condition_to_do.filter(pk=h.pk).exists())
                        if not j.condition_to_do.filter(pk=h.pk).exists():
                            valid = False
                            break
                    if valid:
                        condition = j
                        break

            if condition is not None:
                # adding items to existing condition
                b = get_condition_items(i, condition)
                for j in b:
                    for x in j['old_model'].all():
                        if not j['new_model'].filter(id=x.id).exists():
                            j['new_model'].add(x)
            else:
                # duplicating condition and adding to user
                i.pk = None
                i.sequence = None
                i.save()
                b = get_condition_items(original_record, i)
                for j in b:
                    j['new_model'].set(j['old_model'].all())
                user.conditions.add(i)


class ExternalMessage(models.Model):
    EXTERNAL_TYPE = (
        (0, 'Email'),
        (1, 'Slack'),
        (2, 'Text'),
    )
    PEOPLE_CHOICES = (
        (0, 'New hire'),
        (1, 'Manager'),
        (2, 'Buddy'),
        (3, 'custom')
    )
    name = models.CharField(max_length=240)
    content = models.CharField(max_length=12000, blank=True)
    content_json = models.ManyToManyField(Content)
    send_via = models.IntegerField(choices=EXTERNAL_TYPE)
    send_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    person_type = models.IntegerField(choices=PEOPLE_CHOICES, default=1)

    def email_message(self):
        email_data = []
        for i in self.content_json.filter(type__in=['p', 'quote', 'hr']):
            if i.type == 'p':
                email_data.append({
                    "type": 'p',
                    "text": i.content
                })
            elif i.type == 'quote':
                email_data.append({
                    "type": 'block',
                    "text": i.content
                })
            elif i.type == 'hr':
                email_data.append({
                    "type": 'hr',
                    "text": ''
                })
        return email_data

    def get_user(self, new_hire):
        if self.person_type == 0:
            return new_hire
        elif self.person_type == 1:
            return new_hire.manager
        elif self.person_type == 2:
            return new_hire.buddy
        elif self.person_type == 3:
            return self.send_to


class PendingAdminTask(models.Model):
    name = models.CharField(max_length=500)
    comment = models.CharField(max_length=12500, null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_user')
    option = models.CharField(max_length=12500, choices=NOTIFICATION_CHOICES)
    slack_user = models.CharField(max_length=12500, null=True, blank=True)
    email = models.EmailField(max_length=12500, null=True, blank=True)
    date = models.DateField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)


class Condition(models.Model):
    CONDITION_TYPE = (
        (0, 'after'),
        (1, 'to do'),
        (2, 'before')
    )
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, null=True, related_name='conditions')
    condition_type = models.IntegerField(choices=CONDITION_TYPE, default=0)
    days = models.IntegerField(default=0)
    time = models.TimeField(default='08:00')
    condition_to_do = models.ManyToManyField(ToDo, related_name='condition_to_do')
    to_do = models.ManyToManyField(ToDo)
    badges = models.ManyToManyField(Badge)
    resources = models.ManyToManyField(Resource)
    admin_tasks = models.ManyToManyField(PendingAdminTask)
    external_messages = models.ManyToManyField(ExternalMessage)
    introductions = models.ManyToManyField(Introduction)

    def process_condition(self, user):
        from sequences.serializers import PendingAdminTaskSerializer
        from admin_tasks.models import AdminTaskComment
        items_added = {
            'to_do': [],
            'resources': [],
            'badges': [],
            'introductions': []
        }
        for i in self.to_do.all():
            if not user.to_do.filter(pk=i.pk).exists():
                items_added['to_do'].append(i)
                user.to_do.add(i)

        for i in self.resources.all():
            if not user.resources.filter(pk=i.pk).exists():
                items_added['resources'].append(i)
                user.resources.add(i)

        for i in self.badges.all():
            if not user.badges.filter(pk=i.pk).exists():
                items_added['badges'].append(i)
                user.badges.add(i)

        for i in self.introductions.all():
            if not user.introductions.filter(pk=i.pk).exists():
                items_added['introductions'].append(i)
                user.introductions.add(i)

        for i in self.admin_tasks.all():
            if not AdminTask.objects.filter(new_hire=user, assigned_to=i.assigned_to, name=i.name).exists():
                serializer = PendingAdminTaskSerializer(i).data
                serializer.pop('assigned_to')
                serializer.pop('id')
                comment = serializer.pop('comment')
                task = AdminTask.objects.create(**serializer, assigned_to=i.assigned_to, new_hire=user)
                if comment is not None:
                    AdminTaskComment.objects.create(content=comment, comment_by=task.assigned_to, admin_task=task)

        for i in self.external_messages.all():
            if i.get_user(user) == None:
                continue
            if i.send_via == 0:  # email
                send_sequence_message(i.get_user(user), i.email_message())
            elif i.send_via == 1:  # slack
                s = Slack()
                s.set_user(i.get_user(user))
                blocks = []
                for j in i.content_json.all():
                    blocks.append(j.to_slack_block(user))
                s.send_message(blocks=blocks)
            else:  # text
                if i.get_user(user).phone is not None and i.get_user(user).phone != "":
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        to=i.get_user(user).phone,
                        from_=settings.TWILIO_FROM_NUMBER,
                        body=i.content)

        return items_added
