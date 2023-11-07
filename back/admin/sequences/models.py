from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from twilio.rest import Client

from admin.admin_tasks.models import AdminTask
from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.integrations.models import Integration
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import Resource
from admin.to_do.models import ToDo
from misc.fields import ContentJSONField, EncryptedJSONField
from misc.mixins import ContentMixin
from organization.models import Notification
from slack_bot.models import SlackChannel
from slack_bot.utils import Slack

from admin.sequences.emails import send_sequence_message
from admin.sequences.querysets import ConditionQuerySet


class OnboardingSequenceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=Sequence.Category.ONBOARDING)


class OffboardingSequenceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(category=Sequence.Category.OFFBOARDING)


class Sequence(models.Model):
    class Category(models.IntegerChoices):
        ONBOARDING = 0, _("Onboarding sequence")
        OFFBOARDING = 1, _("Offboarding sequence")

    name = models.CharField(verbose_name=_("Name"), max_length=240)
    auto_add = models.BooleanField(default=False)
    category = models.IntegerField(choices=Category.choices)

    objects = models.Manager()
    onboarding = OnboardingSequenceManager()
    offboarding = OffboardingSequenceManager()

    def __str__(self):
        return self.name

    @property
    def update_url(self):
        return reverse("sequences:update", args=[self.id])

    @property
    def is_onboarding(self):
        return self.category == Sequence.Category.ONBOARDING

    def class_name(self):
        return self.__class__.__name__

    def duplicate(self):
        old_sequence = Sequence.objects.get(pk=self.pk)
        self.pk = None
        self.name = _("%(name)s (duplicate)") % {"name": self.name}
        self.auto_add = False
        self.save()

        admin_tasks = {}
        for condition in old_sequence.conditions.all():
            new_condition, admin_tasks = condition.duplicate(admin_tasks=admin_tasks)
            self.conditions.add(new_condition)
        return self

    def assign_to_user(self, user):
        # adding conditions
        for sequence_condition in self.conditions.all():
            user_condition = None

            # Check what kind of condition it is
            if sequence_condition.condition_type in [
                Condition.Type.BEFORE,
                Condition.Type.AFTER,
            ]:
                # Get the timed based condition or return None if not exist
                user_condition = user.conditions.filter(
                    condition_type=sequence_condition.condition_type,
                    days=sequence_condition.days,
                    time=sequence_condition.time,
                ).first()

            elif sequence_condition.condition_type == Condition.Type.TODO:
                # For to_do items, filter all condition items to find if one matches
                # Both the amount and the todos itself need to match exactly
                conditions = user.conditions.filter(condition_type=Condition.Type.TODO)
                original_condition_to_do_ids = (
                    sequence_condition.condition_to_do.all().values_list(
                        "id", flat=True
                    )
                )

                for condition in conditions:
                    # Quickly check if the amount of items match - if not match, drop
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

            elif sequence_condition.condition_type == Condition.Type.ADMIN_TASK:
                # For admin to do items, filter all condition items to find if one
                # matches. Both the amount and the admin to do itself need to match
                # exactly
                conditions = user.conditions.filter(
                    condition_type=Condition.Type.ADMIN_TASK
                )
                original_condition_admin_tasks_ids = (
                    sequence_condition.condition_admin_tasks.all().values_list(
                        "id", flat=True
                    )
                )

                for condition in conditions:
                    # Quickly check if the amount of items match - if not match, drop
                    if condition.condition_admin_tasks.all().count() != len(  # noqa
                        original_condition_admin_tasks_ids
                    ):
                        continue

                    found_admin_tasks = condition.condition_admin_tasks.filter(
                        id__in=original_condition_admin_tasks_ids
                    ).count()

                    if found_admin_tasks == len(original_condition_admin_tasks_ids):
                        # We found our match. Amount matches AND the admin_tasks match
                        user_condition = condition
                        break
            else:
                # Condition (always just one) that will be assigned directly (type == 3)
                # Just run the condition with the new hire
                sequence_condition.process_condition(user)
                continue

            # Let's add the condition to the new hire. Either through adding it to the
            # exising one or creating a new one
            if user_condition is not None:
                # adding items to existing condition
                user_condition.include_other_condition(sequence_condition)
            else:
                # duplicating condition and adding to user
                # Force getting it, as we are about to duplicate it and set the pk to
                # None
                old_condition = Condition.objects.get(id=sequence_condition.id)

                sequence_condition.pk = None
                sequence_condition.sequence = None
                sequence_condition.save()

                # Add condition to_dos
                sequence_condition.condition_to_do.set(
                    old_condition.condition_to_do.all()
                )

                for condition_admin_task in old_condition.condition_admin_tasks.all():
                    sequence_condition.condition_admin_tasks.add(condition_admin_task)
                # Add all the things that get triggered
                sequence_condition.include_other_condition(old_condition)

                # Add newly created condition back to user
                user.conditions.add(sequence_condition)

    def remove_from_user(self, new_hire):
        from admin.admin_tasks.models import AdminTask

        # get all items from all conditions
        to_dos = ToDo.objects.none()
        badges = Badge.objects.none()
        resources = Resource.objects.none()
        admin_tasks = AdminTask.objects.none()
        external_messages = ExternalMessage.objects.none()
        introductions = Introduction.objects.none()
        preboarding = Preboarding.objects.none()
        appointments = Appointment.objects.none()
        integration_configs = IntegrationConfig.objects.none()

        # TODO: this is going to make a lot of queries, should be optimized
        for condition in self.conditions.all():
            to_dos |= condition.to_do.all()
            badges |= condition.badges.all()
            resources |= condition.resources.all()
            admin_tasks |= condition.admin_tasks.all()
            external_messages |= condition.external_messages.all()
            introductions |= condition.introductions.all()
            preboarding |= condition.preboarding.all()
            appointments |= condition.appointments.all()
            integration_configs |= condition.integration_configs.all()

        # Cycle through new hire's item and remove the ones that aren't supposed to
        # be there
        new_hire.to_do.remove(*to_dos)
        new_hire.badges.remove(*badges)
        new_hire.appointments.remove(*appointments)
        new_hire.preboarding.remove(*preboarding)
        new_hire.introductions.remove(*introductions)

        # Do the same with the conditions
        conditions_to_be_deleted = []
        items = {
            "to_do": to_dos,
            "resources": resources,
            "badges": badges,
            "admin_tasks": admin_tasks,
            "external_messages": external_messages,
            "introductions": introductions,
            "preboarding": preboarding,
            "appointments": appointments,
            "integration_configs": integration_configs,
        }
        for condition in new_hire.conditions.all():
            for field in condition._meta.many_to_many:
                # We only want to remove assigned items, not triggers
                if field.name in ("condition_to_do", "condition_admin_tasks"):
                    continue
                getattr(condition, field.name).remove(*items[field.name])

            if condition.is_empty:
                conditions_to_be_deleted.append(condition.id)

        # Remove all empty conditions
        Condition.objects.filter(id__in=conditions_to_be_deleted).delete()
        # Delete sequence
        Notification.objects.order_by("-created").filter(
            notification_type=Notification.Type.ADDED_SEQUENCE
        ).first().delete()


class ExternalMessageManager(models.Manager):
    def for_new_hire(self):
        return self.get_queryset().filter(
            person_type=ExternalMessage.PersonType.NEWHIRE
        )

    def for_admins(self):
        return self.get_queryset().exclude(
            person_type=ExternalMessage.PersonType.NEWHIRE
        )


class ExternalMessage(ContentMixin, models.Model):
    class Type(models.IntegerChoices):
        EMAIL = 0, _("Email")
        SLACK = 1, _("Slack")
        TEXT = 2, _("Text")

    class PersonType(models.IntegerChoices):
        NEWHIRE = 0, _("New hire")
        MANAGER = 1, _("Manager")
        BUDDY = 2, _("Buddy")
        CUSTOM = 3, _("Custom")
        SLACK_CHANNEL = 4, _("Slack channel")

    name = models.CharField(verbose_name=_("Name"), max_length=240)
    content_json = ContentJSONField(default=dict, verbose_name=_("Content"))
    content = models.CharField(verbose_name=_("Content"), max_length=12000, blank=True)
    send_via = models.IntegerField(verbose_name=_("Send via"), choices=Type.choices)
    send_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Send to"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    send_to_channel = models.ForeignKey(
        SlackChannel,
        verbose_name=_("Slack channel"),
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
        verbose_name=_("For"), choices=PersonType.choices, default=1
    )

    @property
    def is_email_message(self):
        return self.send_via == self.Type.EMAIL

    @property
    def is_slack_message(self):
        return self.send_via == self.Type.SLACK

    @property
    def is_text_message(self):
        return self.send_via == self.Type.TEXT

    @property
    def notification_add_type(self):
        if self.is_text_message:
            return Notification.Type.SENT_TEXT_MESSAGE
        if self.is_email_message:
            return Notification.Type.SENT_EMAIL_MESSAGE
        if self.is_slack_message:
            return Notification.Type.SENT_SLACK_MESSAGE

    @property
    def get_icon_template(self):
        if self.is_email_message:
            return render_to_string("_email_icon.html")
        if self.is_slack_message:
            return render_to_string("_slack_icon.html")
        if self.is_text_message:
            return render_to_string("_text_icon.html")

    def duplicate(self, change_name=False):
        self.pk = None
        self.save()
        return self

    def get_user(self, new_hire):
        if self.person_type == ExternalMessage.PersonType.NEWHIRE:
            return new_hire
        elif self.person_type == ExternalMessage.PersonType.MANAGER:
            return new_hire.manager
        elif self.person_type == ExternalMessage.PersonType.BUDDY:
            return new_hire.buddy
        else:
            return self.send_to

    def execute(self, user):
        if self.is_email_message:
            # Make sure there is actually an email
            if self.get_user(user) is None:
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_NO_EMAIL,
                    extra_text=self.subject,
                    created_for=user,
                )
                return

            send_sequence_message(
                user, self.get_user(user), self.content_json["blocks"], self.subject
            )
        elif self.is_slack_message:
            blocks = []
            # We don't have the model function on this model, so let's get it from a
            # different model. A bit hacky, but should be okay.
            blocks = ToDo(content=self.content_json).to_slack_block(user)

            # Send to channel instead of person?
            if self.person_type == ExternalMessage.PersonType.SLACK_CHANNEL:
                channel = (
                    None
                    if self.send_to_channel is None
                    else "#" + self.send_to_channel.name
                )
            else:
                channel = self.get_user(user).slack_user_id

            Slack().send_message(blocks=blocks, channel=channel)
        else:  # text message
            send_to = self.get_user(user)
            if send_to is None or send_to.phone == "":
                Notification.objects.create(
                    notification_type=Notification.Type.FAILED_NO_PHONE,
                    extra_text=self.name,
                    created_for=user,
                )
                return

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                to=send_to.phone,
                from_=settings.TWILIO_FROM_NUMBER,
                body=self.get_user(user).personalize(self.content),
            )

        if not self.is_slack_message:
            # The Slack send_message function already registered this notification so
            # skip it in that case.
            Notification.objects.create(
                notification_type=self.notification_add_type,
                extra_text=self.name,
                created_for=user,
            )

    objects = ExternalMessageManager()


class PendingEmailMessage(ExternalMessage):
    # Email message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = self.Type.EMAIL
        return super(PendingEmailMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingSlackMessage(ExternalMessage):
    # Slack message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = self.Type.SLACK
        return super(PendingSlackMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingTextMessage(ExternalMessage):
    # Text message model proxied from ExternalMessage

    def save(self, *args, **kwargs):
        self.send_via = self.Type.TEXT
        return super(PendingTextMessage, self).save(*args, **kwargs)

    class Meta:
        proxy = True


class PendingAdminTask(models.Model):
    class PersonType(models.IntegerChoices):
        NEWHIRE = 0, _("New hire")
        MANAGER = 1, _("Manager")
        BUDDY = 2, _("Buddy")
        CUSTOM = 3, _("Custom")

    class Notification(models.IntegerChoices):
        NO = 0, _("No")
        EMAIL = 1, _("Email")
        SLACK = 2, _("Slack")

    name = models.CharField(verbose_name=_("Name"), max_length=500)
    comment = models.CharField(
        verbose_name=_("Comment"), max_length=12500, default="", blank=True
    )
    person_type = models.IntegerField(
        # Filter out new hire. Never assign an admin task to a new hire.
        verbose_name=_("Assigned to"),
        choices=[person for person in PersonType.choices if person[0] != 0],
        default=PersonType.MANAGER,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Pick user"),
        on_delete=models.CASCADE,
        related_name="assigned_user",
        null=True,
    )
    option = models.IntegerField(
        verbose_name=_("Send email or Slack message to extra user?"),
        choices=Notification.choices,
        default=0,
    )
    slack_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Slack user"),
        on_delete=models.SET_NULL,
        related_name="pending_admin_task_slack_user",
        blank=True,
        null=True,
    )
    email = models.EmailField(
        verbose_name=_("Email"), max_length=12500, default="", blank=True
    )
    date = models.DateField(verbose_name=_("Due date"), blank=True, null=True)
    priority = models.IntegerField(
        verbose_name=_("Priority"),
        choices=AdminTask.Priority.choices,
        default=AdminTask.Priority.MEDIUM,
    )
    template = models.BooleanField(
        default=False,
        help_text=(
            "Should always be False, for now it's just here to comply with other "
            "functions (like duplicate)"
        ),
    )

    def __str__(self):
        return self.name

    def get_user(self, new_hire):
        if self.person_type == PendingAdminTask.PersonType.NEWHIRE:
            return new_hire
        elif self.person_type == PendingAdminTask.PersonType.MANAGER:
            return new_hire.manager
        elif self.person_type == PendingAdminTask.PersonType.BUDDY:
            return new_hire.buddy
        else:
            return self.assigned_to

    def execute(self, user):
        from admin.admin_tasks.models import AdminTask

        if AdminTask.objects.filter(new_hire=user, based_on=self).exists():
            # if a task already exists, then skip
            return

        AdminTask.objects.create_admin_task(
            new_hire=user,
            assigned_to=self.get_user(user),
            name=self.name,
            option=self.option,
            slack_user=self.slack_user,
            email=self.email,
            date=self.date,
            priority=self.priority,
            pending_admin_task=self,
            manual_integration=None,
            comment=self.comment,
            send_notification=True,
        )

    @property
    def get_icon_template(self):
        return render_to_string("_admin_task_icon.html")

    def duplicate(self, change_name=False):
        self.pk = None
        self.save()
        return self


class IntegrationConfig(models.Model):
    class PersonType(models.IntegerChoices):
        MANAGER = 1, _("Manager")
        BUDDY = 2, _("Buddy")
        CUSTOM = 3, _("Custom")

    integration = models.ForeignKey(Integration, on_delete=models.CASCADE, null=True)
    additional_data = EncryptedJSONField(default=dict)
    person_type = models.IntegerField(
        verbose_name=_("Assigned to"),
        choices=PersonType.choices,
        null=True,
        blank=True,
        help_text=_(
            "Leave empty to automatically check the integration as created/removed."
        ),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("Pick user"),
        on_delete=models.CASCADE,
        related_name="assigned_user_integration",
        null=True,
        blank=True,
    )

    @property
    def name(self):
        return self.integration.name

    @property
    def get_icon_template(self):
        return render_to_string("_integration_config.html")

    def duplicate(self, change_name=False):
        self.pk = None
        self.save()
        return self

    def execute(self, user):
        # avoid circular import
        from users.models import IntegrationUser

        if not self.integration.skip_user_provisioning:
            # it's an automated integration so just execute it
            self.integration.execute(user, self.additional_data)
            return

        is_offboarding = user.termination_date is not None

        if self.person_type is None:
            # doesn't need extra action, just log
            integration_user, created = IntegrationUser.objects.update_or_create(
                user=user,
                integration=self.integration,
                defaults={"revoked": is_offboarding},
            )

            Notification.objects.create(
                notification_type=Notification.Type.REMOVE_MANUAL_INTEGRATION
                if is_offboarding
                else Notification.Type.ADD_MANUAL_INTEGRATION,
                extra_text=self.integration.name,
                created_for=user,
                item_id=integration_user.id,
                notified_user=False,
                public_to_new_hire=False,
            )

        else:
            # we need an admin to create the item and then check it off
            if self.person_type == IntegrationConfig.PersonType.MANAGER:
                assigned_to = user.manager
            elif self.person_type == IntegrationConfig.PersonType.BUDDY:
                assigned_to = user.buddy
            else:
                assigned_to = self.assigned_to

            admin_task_name = _("Create integration: %(integration_name)s") % {
                "integration_name": self.integration.name
            }

            admin_task = AdminTask.objects.create(
                new_hire=user,
                assigned_to=assigned_to,
                name=admin_task_name,
                option=AdminTask.Notification.NO,
                manual_integration=self.integration,
            )

            Notification.objects.create(
                notification_type=Notification.Type.ADDED_ADMIN_TASK,
                extra_text=admin_task_name,
                created_for=user,
                item_id=admin_task.id,
                notified_user=False,
                public_to_new_hire=False,
            )


class ConditionPrefetchManager(models.Manager):
    def prefetched(self):
        return (
            self.get_queryset()
            .prefetch_related(
                Prefetch("introductions", queryset=Introduction.objects.all()),
                Prefetch("to_do", queryset=ToDo.objects.all().defer("content")),
                Prefetch("resources", queryset=Resource.objects.all()),
                Prefetch(
                    "appointments", queryset=Appointment.objects.all().defer("content")
                ),
                Prefetch("badges", queryset=Badge.objects.all().defer("content")),
                Prefetch(
                    "external_messages",
                    queryset=ExternalMessage.objects.for_new_hire().defer(
                        "content", "content_json"
                    ),
                    to_attr="external_new_hire",
                ),
                Prefetch(
                    "external_messages",
                    queryset=ExternalMessage.objects.for_admins().defer(
                        "content", "content_json"
                    ),
                    to_attr="external_admin",
                ),
                Prefetch(
                    "condition_to_do", queryset=ToDo.objects.all().defer("content")
                ),
                Prefetch("admin_tasks", queryset=PendingAdminTask.objects.all()),
                Prefetch(
                    "preboarding", queryset=Preboarding.objects.all().defer("content")
                ),
                Prefetch(
                    "integration_configs", queryset=IntegrationConfig.objects.all()
                ),
            )
            .alias_days_order()
            .order_by("days_order", "time")
        )


class Condition(models.Model):
    class Type(models.IntegerChoices):
        AFTER = 0, _("After new hire has started")
        TODO = 1, _("Based on one or more to do item(s)")
        BEFORE = 2, _("Before the new hire has started")
        WITHOUT = 3, _("Without trigger")
        ADMIN_TASK = 4, _("Based on one or more admin tasks")

    sequence = models.ForeignKey(
        Sequence, on_delete=models.CASCADE, null=True, related_name="conditions"
    )
    condition_type = models.IntegerField(
        verbose_name=_("Block type"), choices=Type.choices, default=Type.AFTER
    )
    days = models.IntegerField(verbose_name=_("Amount of days before/after"), default=1)
    time = models.TimeField(verbose_name=_("At"), default="08:00")
    condition_to_do = models.ManyToManyField(
        ToDo,
        verbose_name=_("Trigger after these to do items have been completed:"),
        related_name="condition_to_do",
    )
    condition_admin_tasks = models.ManyToManyField(
        PendingAdminTask,
        verbose_name=_("Trigger after these admin todo items have been completed:"),
        related_name="condition_triggers",
    )
    to_do = models.ManyToManyField(ToDo)
    badges = models.ManyToManyField(Badge)
    resources = models.ManyToManyField(Resource)
    admin_tasks = models.ManyToManyField(PendingAdminTask)
    external_messages = models.ManyToManyField(ExternalMessage)
    introductions = models.ManyToManyField(Introduction)
    preboarding = models.ManyToManyField(Preboarding)
    appointments = models.ManyToManyField(Appointment)
    integration_configs = models.ManyToManyField(IntegrationConfig)

    objects = ConditionPrefetchManager.from_queryset(ConditionQuerySet)()

    @property
    def is_empty(self):
        return not (
            self.to_do.exists()
            or self.badges.exists()
            or self.resources.exists()
            or self.admin_tasks.exists()
            or self.introductions.exists()
            or self.external_messages.exists()
            or self.preboarding.exists()
            or self.appointments.exists()
            or self.integration_configs.exists()
        )

    @property
    def based_on_to_do(self):
        return self.condition_type == Condition.Type.TODO

    @property
    def based_on_admin_task(self):
        return self.condition_type == Condition.Type.ADMIN_TASK

    @property
    def based_on_time(self):
        return self.condition_type in [Condition.Type.AFTER, Condition.Type.BEFORE]

    def remove_item(self, model_item):
        # If any of the external messages, then get the root one
        if type(model_item)._meta.model_name in [
            "pendingemailmessage",
            "pendingslackmessage",
            "pendingtextmessage",
        ]:
            model_item = ExternalMessage.objects.get(pk=model_item.id)
        # model_item is a template item. I.e. a ToDo object.
        for field in self._meta.many_to_many:
            # We only want to remove assigned items, not triggers
            if field.name in ("condition_to_do", "condition_admin_tasks"):
                continue
            if (
                field.related_model._meta.model_name
                == type(model_item)._meta.model_name
            ):
                getattr(self, field.name).remove(model_item)

    def add_item(self, model_item):
        # model_item is a template item. I.e. a ToDo object.
        for field in self._meta.many_to_many:
            # We only want to add assigned items, not triggers
            if field.name in ("condition_to_do", "condition_admin_tasks"):
                continue
            if (
                field.related_model._meta.model_name
                == type(model_item)._meta.model_name
            ):
                getattr(self, field.name).add(model_item)

    def include_other_condition(self, condition):
        # this will put another condition into this one
        for field in self._meta.many_to_many:
            # We only want to add assigned items, not triggers
            if field.name in ("condition_to_do", "condition_admin_tasks"):
                continue

            condition_field = getattr(condition, field.name)
            for item in condition_field.all():
                getattr(self, field.name).add(item)

    def duplicate(self, admin_tasks):
        old_condition = Condition.objects.get(id=self.id)
        self.pk = None
        self.save()

        # This function is not being used except for duplicating sequences
        # It can't be triggered standalone (for now)
        for field in old_condition._meta.many_to_many:
            if field.name not in [
                "admin_tasks",
                "condition_admin_tasks",
                "external_messages",
                "integration_configs",
            ]:
                # Duplicate template items that have been customized. Those should be
                # unique again. (only items that have a `template` flag on the model)
                items = []
                old_custom_templates = getattr(old_condition, field.name).filter(
                    template=False
                )
                for old in old_custom_templates:
                    dup = old.duplicate(change_name=False)
                    items.append(dup)

                # Reassign items that are still unchanged templates, they should connect
                # to the same item
                old_templates = getattr(old_condition, field.name).filter(template=True)
                getattr(self, field.name).add(*old_templates, *items)

            else:
                # For items that do not have templates, just duplicate them
                items = []
                old_custom_templates = getattr(old_condition, field.name).all()
                # exception for condition_admin_tasks, those should be linked to
                # previously created items, so link old id to new object, for
                # future lookup
                if field.name == "condition_admin_tasks":
                    for item in old_custom_templates:
                        items.append(admin_tasks[item.id])

                else:
                    for old in old_custom_templates:
                        old_id = old.id
                        dup = old.duplicate(change_name=False)
                        items.append(dup)
                        if field.name == "admin_tasks":
                            # lookup old id to get newly created object
                            admin_tasks[old_id] = dup

                getattr(self, field.name).add(*items)

        # returning the new item
        return self, admin_tasks

    def process_condition(self, user, skip_notification=False):
        # avoid circular import

        # Loop over all m2m fields and add the ones that can be easily added
        for field in [
            "to_do",
            "resources",
            "badges",
            "appointments",
            "introductions",
            "preboarding",
        ]:
            for item in getattr(self, field).all():
                getattr(user, field).add(item)

                Notification.objects.create(
                    notification_type=item.notification_add_type,
                    extra_text=item.name,
                    created_for=user,
                    item_id=item.id,
                    notified_user=skip_notification,
                    public_to_new_hire=True,
                )

        # For the ones that aren't a quick copy/paste, follow back to their model and
        # execute them. It will also add an item to the notification model there.
        for field in ["admin_tasks", "external_messages", "integration_configs"]:
            for item in getattr(self, field).all():
                item.execute(user)
