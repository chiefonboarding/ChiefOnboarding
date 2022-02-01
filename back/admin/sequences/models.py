from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.urls import reverse
from twilio.rest import Client

from admin.admin_tasks.models import NOTIFICATION_CHOICES, PRIORITY_CHOICES, AdminTask
from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import Resource
from admin.sequences.utils import get_condition_items
from admin.to_do.models import ToDo
from misc.models import Content
from misc.serializers import FileSerializer
from slack_bot.slack import Slack

from .emails import send_sequence_message


class Sequence(models.Model):
    name = models.CharField(max_length=240)
    auto_add = models.BooleanField(default=False)

    def update_url(self):
        return reverse("sequences:update", args=[self.id])

    def class_name(self):
        return self.__class__.__name__

    def duplicate(self):
        old_sequence = Sequence.objects.get(pk=self.pk)
        self.pk = None
        self.name = self.name + " (duplicate)"
        self.save()
        for condition in old_sequence.conditions.all():
            new_condition = condition.duplicate()
            self.conditions.add(new_condition)
        return self

    def assign_to_user(self, user):
        user_condition = None

        # adding conditions
        for sequence_condition in self.conditions.all():
            # Check what kind of condition it is
            if sequence_condition.condition_type in [0, 2]:
                # Get the timed based condition or return None if not exist
                user_condition = user.conditions.filter(
                    condition_type=sequence_condition.condition_type,
                    days=sequence_condition.days,
                ).first()

            elif sequence_condition.condition_type == 1:
                # For to_do items, filter all condition items to find if one matches
                # Both the amount and the todos itself need to match exactly
                conditions = user.conditions.filter(condition_type=1)
                original_condition_to_do_ids = sequence_condition.condition_to_do.all().values_list("id", flat=True)
                for condition in conditions:
                    # Quickly check if the amount of items match - if not match, then drop
                    if condition.condition_to_do.all().count() != len(original_condition_to_do_ids):
                        continue

                    found_to_do_items = condition.condition_to_do.filter(id__in=original_condition_to_do_ids).count()
                    if found_to_do_items == len(original_condition_to_do_ids):
                        # We found our match. Amount matches AND the todos match
                        user_condition = condition
                        break
            else:
                # Condition is the unconditional one. Check if exists, otherwise create and
                user_condition = user.conditions.get(condition_type=3)

            # Let's add the condition to the new hire. Either through adding it to the exising one
            # or creating a new one
            if user_condition is not None:
                # adding items to existing condition
                user_condition.include_other_condition(sequence_condition)
            else:
                # duplicating condition and adding to user
                # Force getting it, as we are about to duplicate it and set the pk to None
                old_condition = Condition.objects.get(id=sequence_condition.id)

                sequence_condition.pk = None
                sequence_condition.sequence = None
                sequence_condition.save()
                sequence_condition.include_other_condition(old_condition)

                # Add newly created condition back to user
                user.conditions.add(sequence_condition)


class ExternalMessageManager(models.Manager):
    def for_new_hire(self):
        return self.filter(person_type=0)

    def for_admins(self):
        return self.exclude(person_type=0)


class ExternalMessage(models.Model):
    EXTERNAL_TYPE = (
        (0, "Email"),
        (1, "Slack"),
        (2, "Text"),
    )
    PEOPLE_CHOICES = ((0, "New hire"), (1, "Manager"), (2, "Buddy"), (3, "custom"))
    name = models.CharField(max_length=240)
    content = models.CharField(max_length=12000, blank=True)
    content_json = models.ManyToManyField(Content)
    send_via = models.IntegerField(choices=EXTERNAL_TYPE)
    send_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True
    )
    subject = models.CharField(max_length=78, default="Here is an update!", blank=True)
    person_type = models.IntegerField(choices=PEOPLE_CHOICES, default=1)

    def duplicate(self):
        self.pk = None
        self.save()
        return self

    def email_message(self):
        email_data = []
        for i in self.content_json.filter(
            type__in=["p", "quote", "hr", "ul", "ol", "h1", "h2", "h3", "image", "file"]
        ):
            if i.type == "quote":
                email_data.append({"type": "block", "text": i.content})
            else:
                files = []
                if i.files.all().exists():
                    files = FileSerializer(i.files.all(), many=True).data
                email_data.append(
                    {
                        "type": i.type,
                        "text": i.content,
                        "items": i.items,
                        "files": files,
                    }
                )
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

    @property
    def is_email_message(self):
        return self.send_via == 0

    @property
    def is_slack_message(self):
        return self.send_via == 1

    @property
    def is_text_message(self):
        return self.send_via == 2

    @property
    def get_icon_template(self):
        if self.is_email_message:
            return render_to_string("_email_icon.html")
        if self.is_slack_message:
            return render_to_string("_slack_icon.html")
        if self.is_text_message:
            return render_to_string("_text_icon.html")

    objects = ExternalMessageManager()


class PendingAdminTask(models.Model):
    name = models.CharField(max_length=500)
    comment = models.CharField(max_length=12500, default="", blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_user"
    )
    option = models.CharField(max_length=12500, choices=NOTIFICATION_CHOICES)
    slack_user = models.CharField(max_length=12500, default="", blank=True)
    email = models.EmailField(max_length=12500, default="", blank=True)
    date = models.DateField(blank=True, null=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)

    @property
    def get_icon_template(self):
        return render_to_string("_admin_task_icon.html")

    def duplicate(self):
        self.pk = None
        self.save()
        return self


class AccountProvision(models.Model):
    INTEGRATION_OPTIONS = (
        ("asana", "Add Asana account to team"),
        ("google", "Create Google account"),
        ("slack", "Create Slack account"),
    )
    integration_type = models.CharField(max_length=10, choices=INTEGRATION_OPTIONS)
    additional_data = models.JSONField(models.TextField(blank=True), default=dict)

    def duplicate(self):
        self.pk = None
        self.save()
        return self

class Condition(models.Model):
    CONDITION_TYPE = (
        (0, "After new hire has started"),
        (1, "Based on one or more to do item(s)"),
        (2, "Before the new hire has started"),
        (3, "Without trigger"),
    )
    sequence = models.ForeignKey(
        Sequence, on_delete=models.CASCADE, null=True, related_name="conditions"
    )
    condition_type = models.IntegerField(choices=CONDITION_TYPE, default=0)
    days = models.IntegerField(default=0)
    time = models.TimeField(default="08:00")
    condition_to_do = models.ManyToManyField(ToDo, related_name="condition_to_do")
    to_do = models.ManyToManyField(ToDo)
    badges = models.ManyToManyField(Badge)
    resources = models.ManyToManyField(Resource)
    admin_tasks = models.ManyToManyField(PendingAdminTask)
    external_messages = models.ManyToManyField(ExternalMessage)
    introductions = models.ManyToManyField(Introduction)
    preboarding = models.ManyToManyField(Preboarding)
    appointments = models.ManyToManyField(Appointment)
    account_provisions = models.ManyToManyField(AccountProvision)

    def remove_item(self, model_item):
        # model_item is a template item. I.e. a ToDo object.
        for field in self._meta.many_to_many:
            # We only want to remove assigned items, not triggers
            if field.name == "condition_to_do":
                continue
            if (
                field.related_model._meta.model_name
                == type(model_item)._meta.model_name
            ):
                self.__getattribute__(field.name).remove(model_item)

    def add_item(self, model_item):
        # model_item is a template item. I.e. a ToDo object.
        for field in self._meta.many_to_many:
            # We only want to add assigned items, not triggers
            if field.name == "condition_to_do":
                continue
            if (
                field.related_model._meta.model_name
                == type(model_item)._meta.model_name
            ):
                self.__getattribute__(field.name).add(model_item)

    def include_other_condition(self, condition):
        # this will put another condition into this one
        for field in self._meta.many_to_many:
            # We only want to add assigned items, not triggers
            if field.name == "condition_to_do":
                continue

            condition_field = condition.__getattribute__(field.name)
            for item in condition_field.all():
                self.__getattribute__(field.name).add(item)


    def duplicate(self):
        old_condition = Condition.objects.get(id=self.id)
        self.pk = None
        self.save()
        # This function is not being used except for duplicating sequences
        # It can't be triggered standalone (for now)
        for field in old_condition._meta.many_to_many:

            if field.name not in ['admin_tasks', 'external_messages', 'account_provisions']:
                # Duplicate old ones
                old_custom_templates = old_condition.__getattribute__(field.name).filter(template=False)
                for old in old_custom_templates:
                    dup = old.duplicate()
                    self.__getattribute__(field.name).add(dup)

                # Only using set() for template items. The other ones need to be duplicated as they are unique to the condition
                old_templates = old_condition.__getattribute__(field.name).filter(template=True)
                self.__getattribute__(field.name).set(old_templates)

            else:
                # For items that do not have templates, just duplicate them
                old_custom_templates = old_condition.__getattribute__(field.name).all()
                for old in old_custom_templates:
                    dup = old.duplicate()
                    self.__getattribute__(field.name).add(dup)

        # returning the new item
        return self


    def process_condition(self, user):
        from admin_tasks.models import AdminTaskComment
        from sequences.serializers import PendingAdminTaskSerializer

        items_added = {"to_do": [], "resources": [], "badges": [], "introductions": []}
        for i in self.to_do.all():
            if not user.to_do.filter(pk=i.pk).exists():
                items_added["to_do"].append(i)
                user.to_do.add(i)

        for i in self.resources.all():
            if not user.resources.filter(pk=i.pk).exists():
                items_added["resources"].append(i)
                user.resources.add(i)

        for i in self.badges.all():
            if not user.badges.filter(pk=i.pk).exists():
                items_added["badges"].append(i)
                user.badges.add(i)

        for i in self.introductions.all():
            if not user.introductions.filter(pk=i.pk).exists():
                items_added["introductions"].append(i)
                user.introductions.add(i)

        for i in self.admin_tasks.all():
            if not AdminTask.objects.filter(
                new_hire=user, assigned_to=i.assigned_to, name=i.name
            ).exists():
                serializer = PendingAdminTaskSerializer(i).data
                serializer.pop("assigned_to")
                serializer.pop("id")
                comment = serializer.pop("comment")
                task = AdminTask.objects.create(
                    **serializer, assigned_to=i.assigned_to, new_hire=user
                )
                if comment is not None:
                    AdminTaskComment.objects.create(
                        content=comment, comment_by=task.assigned_to, admin_task=task
                    )

        for i in self.external_messages.all():
            if i.get_user(user) is None:
                continue
            if i.send_via == 0:  # email
                try:
                    send_sequence_message(
                        i.get_user(user), i.email_message(), i.subject
                    )
                except:
                    pass
            elif i.send_via == 1:  # slack
                s = Slack()
                s.set_user(i.get_user(user))
                blocks = []
                for j in i.content_json.all():
                    blocks.append(j.to_slack_block(user))
                s.send_message(blocks=blocks)
            else:  # text
                if i.get_user(user).phone != "":
                    client = Client(
                        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                    )
                    client.messages.create(
                        to=i.get_user(user).phone,
                        from_=settings.TWILIO_FROM_NUMBER,
                        body=i.content,
                    )

        return items_added
