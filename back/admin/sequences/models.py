from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from twilio.rest import Client

from admin.admin_tasks.models import NOTIFICATION_CHOICES, PRIORITY_CHOICES
from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import Resource
from admin.to_do.models import ToDo
from misc.fields import ContentJSONField
from misc.serializers import FileSerializer
from organization.models import Notification
from slack_bot.slack import Slack

from .emails import send_sequence_message


class Sequence(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=240)
    auto_add = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def update_url(self):
        return reverse("sequences:update", args=[self.id])

    def class_name(self):
        return self.__class__.__name__

    def duplicate(self):
        old_sequence = Sequence.objects.get(pk=self.pk)
        self.pk = None
        self.name = _("%(name)s (duplicate)") % {"name": self.name}
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
                original_condition_to_do_ids = (
                    sequence_condition.condition_to_do.all().values_list(
                        "id", flat=True
                    )
                )
                for condition in conditions:
                    # Quickly check if the amount of items match - if not match, then drop
                    if condition.condition_to_do.all().count() != len(
                        original_condition_to_do_ids
                    ):
                        continue

                    found_to_do_items = condition.condition_to_do.filter(
                        id__in=original_condition_to_do_ids
                    ).count()
                    if found_to_do_items == len(original_condition_to_do_ids):
                        # We found our match. Amount matches AND the todos match
                        user_condition = condition
                        break
            else:
                # Condition is the unconditional one. Add them directly to the new hire
                # Needs to be rewritten to clean it up
                for preboarding in sequence_condition.preboarding.all():
                    user.preboarding.add(preboarding)
                for todo in sequence_condition.to_do.all():
                    user.to_do.add(todo)
                for resource in sequence_condition.resources.all():
                    user.resources.add(resource)
                for intro in sequence_condition.introductions.all():
                    user.introductions.add(intro)

                continue

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
        (0, _("Email")),
        (1, _("Slack")),
        (2, _("Text")),
    )
    PEOPLE_CHOICES = (
        (0, _("New hire")),
        (1, _("Manager")),
        (2, _("Buddy")),
        (3, _("custom")),
    )
    name = models.CharField(verbose_name=_("Name"), max_length=240)
    content_json = ContentJSONField(default=dict, verbose_name=_("Content"))
    content = models.CharField(verbose_name=_("Content"), max_length=12000, blank=True)
    send_via = models.IntegerField(verbose_name=_("Send via"), choices=EXTERNAL_TYPE)
    send_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Send to"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=78,
        default=_("Here is an update!"),
        blank=True,
    )
    person_type = models.IntegerField(
        verbose_name=_("Person type"), choices=PEOPLE_CHOICES, default=1
    )

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
    def notification_add_type(self):
        if self.is_text_message:
            return "sent_text_message"
        if self.is_email_message:
            return "sent_email_message"
        if self.is_slack_message:
            return "sent_slack_message"

    @property
    def get_icon_template(self):
        if self.is_email_message:
            return render_to_string("_email_icon.html")
        if self.is_slack_message:
            return render_to_string("_slack_icon.html")
        if self.is_text_message:
            return render_to_string("_text_icon.html")

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
        else:
            return self.send_to

    def execute(self, user):
        if self.is_email_message:
            try:
                send_sequence_message(
                    self.get_user(user), self.email_message(), self.subject
                )
            except:
                pass
        elif self.is_slack_message:
            s = Slack()
            s.set_user(self.get_user(user))
            blocks = []
            # We don't have the model function on this model, so let's get it from a
            # different model. A bit hacky, but should be okay.
            blocks = ToDo(content=self.content_json).to_slack_block(user)
            s.send_message(blocks=blocks)
        else:  # text message
            phone_number = self.get_user(user).phone
            if phone_number == "":
                Notification.objects.create(
                    notification_type="failed_no_phone",
                    extra_text=self.name,
                    created_for=self.get_user(user),
                )
                return

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=phone_number,
                from_=settings.TWILIO_FROM_NUMBER,
                body=self.content,
            )

        Notification.objects.create(
            notification_type=self.notification_add_type,
            extra_text=self.name,
            created_for=self.get_user(user),
        )

    objects = ExternalMessageManager()


class PendingEmailMessage(ExternalMessage):
    # Email message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = 0
        return super(PendingEmailMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingSlackMessage(ExternalMessage):
    # Slack message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = 1
        return super(PendingSlackMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingTextMessage(ExternalMessage):
    # Text message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = 2
        return super(PendingTextMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingAdminTask(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=500)
    comment = models.CharField(
        verbose_name=_("Comment"), max_length=12500, default="", blank=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Assigned to"),
        on_delete=models.CASCADE,
        related_name="assigned_user",
    )
    option = models.CharField(
        verbose_name=_("Option"), max_length=12500, choices=NOTIFICATION_CHOICES
    )
    slack_user = models.CharField(
        verbose_name=_("Slack option"), max_length=12500, default="", blank=True
    )
    email = models.EmailField(
        verbose_name=_("Email"), max_length=12500, default="", blank=True
    )
    date = models.DateField(verbose_name=_("Due date"), blank=True, null=True)
    priority = models.IntegerField(
        verbose_name=_("Priority"), choices=PRIORITY_CHOICES, default=2
    )

    def execute(self, user):
        from admin.admin_tasks.models import AdminTask, AdminTaskComment

        admin_task, created = AdminTask.objects.get_or_create(
            new_hire=user,
            assigned_to=self.assigned_to,
            name=self.name,
            defaults={
                "option": self.option,
                "slack_user": self.slack_user,
                "email": self.email,
                "date": self.date,
                "priority": self.priority,
            },
        )
        if created and self.comment != "":
            AdminTaskComment.objects.create(
                content=self.comment,
                comment_by=admin_task.assigned_to,
                admin_task=admin_task,
            )

        Notification.objects.create(
            notification_type="added_admin_task",
            extra_text=self.name,
            created_for=self.assigned_to,
        )

    @property
    def get_icon_template(self):
        return render_to_string("_admin_task_icon.html")

    def duplicate(self):
        self.pk = None
        self.save()
        return self


class AccountProvision(models.Model):
    INTEGRATION_OPTIONS = (
        ("asana", _("Add Asana account to team")),
        ("google", _("Create Google account")),
        ("slack", _("Create Slack account")),
    )
    integration_type = models.CharField(max_length=10, choices=INTEGRATION_OPTIONS)
    additional_data = models.JSONField(models.TextField(blank=True), default=dict)

    def duplicate(self):
        self.pk = None
        self.save()
        return self


class Condition(models.Model):
    CONDITION_TYPE = (
        (0, _("After new hire has started")),
        (1, _("Based on one or more to do item(s)")),
        (2, _("Before the new hire has started")),
        (3, _("Without trigger")),
    )
    sequence = models.ForeignKey(
        Sequence, on_delete=models.CASCADE, null=True, related_name="conditions"
    )
    condition_type = models.IntegerField(
        verbose_name=_("Block type"), choices=CONDITION_TYPE, default=0
    )
    days = models.IntegerField(
        verbose_name=_("Amount of days before/after new hire has started"), default=0
    )
    time = models.TimeField(verbose_name=_("At"), default="08:00")
    condition_to_do = models.ManyToManyField(
        ToDo,
        verbose_name=_("Trigger after these to do items have been completed:"),
        related_name="condition_to_do",
    )
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

            if field.name not in [
                "admin_tasks",
                "external_messages",
                "account_provisions",
            ]:
                # Duplicate old ones
                old_custom_templates = old_condition.__getattribute__(
                    field.name
                ).filter(template=False)
                for old in old_custom_templates:
                    dup = old.duplicate()
                    self.__getattribute__(field.name).add(dup)

                # Only using set() for template items. The other ones need to be
                # duplicated as they are unique to the condition
                old_templates = old_condition.__getattribute__(field.name).filter(
                    template=True
                )
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
        # Loop over all m2m fields and add the ones that can be easily added
        for field in [
            "to_do",
            "resources",
            "badges",
            "appointments",
            "introductions",
            "preboarding",
        ]:
            for item in self.__getattribute__(field).all():
                user.__getattribute__(field).add(item)

                Notification.objects.create(
                    notification_type=item.notification_add_type,
                    extra_text=item.name,
                    created_for=user,
                )

        # For the ones that aren't a quick copy/paste, follow back to their model and execute them
        for field in ["admin_tasks", "external_messages", "account_provisions"]:
            for item in self.__getattribute__(field).all():
                item.execute(user)
