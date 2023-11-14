import uuid
from datetime import datetime, timedelta

import pyotp
import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import CheckConstraint, Q
from django.template import Context, Template
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property, lazy
from django.utils.translation import gettext_lazy as _

from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.hardware.models import Hardware
from admin.integrations.models import Integration
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import CourseAnswer, Resource
from admin.sequences.models import Condition
from admin.to_do.models import ToDo
from misc.fernet_fields import EncryptedTextField
from misc.models import File
from organization.models import Notification
from slack_bot.utils import Slack, paragraph

from .utils import CompletedFormCheck


class Department(models.Model):
    """
    Department that has been attached to a user
    At the moment, only one department per user
    """

    name = models.TextField()

    def __str__(self):
        return "%s" % self.name


class CustomUserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        # Make validation case sensitive
        return self.get(**{self.model.USERNAME_FIELD + "__iexact": email})


class ManagerSlackManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(
            role__in=[User.Role.MANAGER, User.Role.ADMIN]
        ) | super().get_queryset().exclude(slack_user_id="")


class OffboardingManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(termination_date__isnull=False)


class ManagerManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(role__in=[User.Role.MANAGER, User.Role.ADMIN])
        )

    def with_slack(self):
        return self.get_queryset().exclude(slack_user_id="")


class NewHireManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(role=User.Role.NEWHIRE, termination_date__isnull=True)
        )

    def without_slack(self):
        return self.get_queryset().filter(slack_user_id="")

    def with_slack(self):
        return self.get_queryset().exclude(slack_user_id="")

    def starting_today(self):
        return (
            self.get_queryset().filter(start_day=datetime.now().date()).order_by("id")
        )

    def to_introduce(self):
        return self.get_queryset().filter(
            is_introduced_to_colleagues=False, start_day__gte=datetime.now().date()
        )


class AdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=get_user_model().Role.ADMIN)


class User(AbstractBaseUser):
    class Role(models.IntegerChoices):
        NEWHIRE = 0, _("New hire")
        ADMIN = 1, _("Administrator")
        MANAGER = 2, _("Manager")
        OTHER = 3, _("Other")

    first_name = models.CharField(verbose_name=_("First name"), max_length=200)
    last_name = models.CharField(verbose_name=_("Last name"), max_length=200)
    email = models.EmailField(verbose_name=_("Email"), max_length=200, unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    birthday = models.DateField(verbose_name=_("Birthday"), default=None, null=True)
    position = models.CharField(
        verbose_name=_("Position"), max_length=300, default="", blank=True
    )
    phone = models.CharField(
        verbose_name=_("Phone"), max_length=300, default="", blank=True
    )
    slack_user_id = models.CharField(max_length=100, default="", blank=True)
    slack_channel_id = models.CharField(max_length=100, default="", blank=True)
    message = models.TextField(verbose_name=_("Message"), default="", blank=True)
    profile_image = models.ForeignKey(
        File, verbose_name=_("Profile image"), on_delete=models.CASCADE, null=True
    )
    linkedin = models.CharField(
        verbose_name=_("Linkedin"), default="", max_length=100, blank=True
    )
    facebook = models.CharField(
        verbose_name=_("Facebook"), default="", max_length=100, blank=True
    )
    twitter = models.CharField(
        verbose_name=_("Twitter"), default="", max_length=100, blank=True
    )
    timezone = models.CharField(
        verbose_name=_("Timezone"),
        default="",
        max_length=1000,
        choices=[(x, x) for x in pytz.common_timezones],
    )
    department = models.ForeignKey(
        Department, verbose_name=_("Department"), on_delete=models.SET_NULL, null=True
    )
    language = models.CharField(
        verbose_name=_("Language"),
        default="en",
        choices=settings.LANGUAGES,
        max_length=5,
    )
    role = models.IntegerField(
        verbose_name=_("Role"),
        choices=Role.choices,
        default=3,
        help_text=_(
            "An administrator has access to everything. A manager has only access to "
            "their new hires and their tasks."
        ),
    )
    is_active = models.BooleanField(default=True)
    is_introduced_to_colleagues = models.BooleanField(default=False)
    sent_preboarding_details = models.BooleanField(default=False)
    totp_secret = EncryptedTextField(blank=True)
    requires_otp = models.BooleanField(default=False)
    seen_updates = models.DateTimeField(auto_now_add=True)
    # new hire specific
    completed_tasks = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    buddy = models.ForeignKey(
        "self",
        verbose_name=_("Buddy"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="new_hire_buddy",
    )
    manager = models.ForeignKey(
        "self",
        verbose_name=_("Manager"),
        on_delete=models.SET_NULL,
        null=True,
        related_name="new_hire_manager",
    )
    start_day = models.DateField(
        verbose_name=_("Start date"),
        null=True,
        blank=True,
        help_text=_("First working day"),
    )
    termination_date = models.DateField(
        verbose_name=_("Termination date"),
        null=True,
        blank=True,
        help_text=_("Last day of working"),
    )
    unique_url = models.CharField(max_length=250, unique=True)
    extra_fields = models.JSONField(default=dict)

    to_do = models.ManyToManyField(ToDo, through="ToDoUser", related_name="user_todos")
    introductions = models.ManyToManyField(
        Introduction, related_name="user_introductions"
    )
    resources = models.ManyToManyField(
        Resource, through="ResourceUser", related_name="user_resources"
    )
    appointments = models.ManyToManyField(Appointment, related_name="user_appointments")
    preboarding = models.ManyToManyField(
        Preboarding, through="PreboardingUser", related_name="user_preboardings"
    )
    badges = models.ManyToManyField(Badge, related_name="user_introductions")
    hardware = models.ManyToManyField(Hardware, related_name="user_hardware")
    integrations = models.ManyToManyField(
        "integrations.Integration",
        through="IntegrationUser",
        related_name="user_integrations",
    )

    # Conditions copied over from chosen sequences
    conditions = models.ManyToManyField(Condition)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()
    managers_and_admins = ManagerManager()
    managers_and_admins_or_slack_users = ManagerSlackManager()
    new_hires = NewHireManager()
    admins = AdminManager()
    offboarding = OffboardingManager()
    ordering = ("first_name",)

    class Meta:
        constraints = [
            CheckConstraint(
                check=~Q(unique_url=""),
                name="unique_url_not_empty",
            )
        ]

    @cached_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @cached_property
    def progress(self):
        if self.completed_tasks == 0 or self.total_tasks == 0:
            return 0
        return (self.completed_tasks / self.total_tasks) * 100

    @cached_property
    def initials(self):
        initial_characters = ""
        if len(self.first_name):
            initial_characters += self.first_name[0]
        if len(self.last_name):
            initial_characters += self.last_name[0]
        return initial_characters

    @property
    def has_slack_account(self):
        return self.slack_user_id != ""

    @cached_property
    def has_new_hire_notifications(self):
        # Notification bell badge on new hire pages
        last_notification = self.notification_receivers.latest("created")
        if last_notification is not None:
            return last_notification.created > self.seen_updates
        return False

    @cached_property
    def missing_extra_info(self):
        extra_info = self.conditions.filter(
            integration_configs__isnull=False,
            integration_configs__integration__manifest__extra_user_info__isnull=False,
        ).values_list(
            "integration_configs__integration__manifest__extra_user_info", flat=True
        )

        # We now have arrays within extra_info: [[{..}], [{..}, {..}]]. Let's make one
        # array with all items: [{..}, {..}, {..}] and remove the duplicates.
        # Loop through both arrays and then add it, if it doesn't exist already.
        # Do the check on the ID, so other props could be different, but it still
        # wouldn't show it.
        extra_user_info = []
        for requested_info_arr in extra_info:
            for requested_info in requested_info_arr:
                if requested_info["id"] not in [item["id"] for item in extra_user_info]:
                    extra_user_info.append(requested_info)

        # Only return what we still need
        return [
            item
            for item in extra_user_info
            if item["id"] not in self.extra_fields.keys()
        ]

    @property
    def requires_manager_or_buddy(self):
        # not all items have to be checked. Introductions for example, doesn't have a
        # content field.
        to_check = [
            "to_do",
            "resources",
            "appointments",
            "badges",
            "hardware",
            "external_messages",
            "admin_tasks",
            "preboarding",
            "integration_configs",
        ]
        requires_manager = False
        requires_buddy = False
        for item in self.conditions.prefetched().prefetch_related(
            "integration_configs__integration"
        ):
            for field in to_check:
                condition_attribute = getattr(item, field)
                for i in condition_attribute.all():
                    if (
                        field == "integration_configs"
                        and i.integration.manifest_type
                        == Integration.ManifestType.WEBHOOK
                    ):
                        (
                            item_requires_manager,
                            item_requires_buddy,
                        ) = i.integration.requires_assigned_manager_or_buddy
                    else:
                        (
                            item_requires_manager,
                            item_requires_buddy,
                        ) = i.requires_assigned_manager_or_buddy

                    if item_requires_manager:
                        requires_manager = True
                    if item_requires_buddy:
                        requires_buddy = True

                    # stop if both are required, no need to go further
                    if requires_manager and requires_buddy:
                        break

        return {"manager": requires_manager, "buddy": requires_buddy}

    def update_progress(self):
        all_to_do_ids = list(
            self.conditions.values_list("to_do__id", flat=True)
        ) + list(self.to_do.values_list("id", flat=True))
        all_course_ids = list(
            self.conditions.filter(resources__course=True).values_list(
                "resources__id", flat=True
            )
        ) + list(self.resources.filter(course=True).values_list("id", flat=True))

        # remove duplicates
        all_to_do_ids = list(dict.fromkeys(all_to_do_ids))
        all_course_ids = list(dict.fromkeys(all_course_ids))

        completed_to_dos = ToDoUser.objects.filter(user=self, completed=True).count()
        completed_courses = ResourceUser.objects.filter(
            resource__course=True, user=self, completed_course=True
        ).count()

        self.total_tasks = len(all_to_do_ids + all_course_ids)
        self.completed_tasks = completed_to_dos + completed_courses
        self.save()

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        if not self.pk:
            self.totp_secret = pyotp.random_base32()
            while True:
                unique_string = get_random_string(length=8)
                if not User.objects.filter(unique_url=unique_string).exists():
                    break
            self.unique_url = unique_string
        super(User, self).save(*args, **kwargs)

    def add_sequences(self, sequences):
        for sequence in sequences:
            sequence.assign_to_user(self)
            Notification.objects.create(
                notification_type=Notification.Type.ADDED_SEQUENCE,
                item_id=sequence.id,
                created_for=self,
                extra_text=sequence.name,
            )

    def remove_sequence(self, sequence):
        sequence.remove_from_user(self)

    @cached_property
    def workday(self):
        start_day = self.start_day
        local_day = self.get_local_time().date()

        if start_day > local_day:
            return 0

        amount_of_workdays = 1
        while local_day != start_day:
            start_day += timedelta(days=1)
            if start_day.weekday() not in [5, 6]:
                amount_of_workdays += 1

        return amount_of_workdays

    def workday_to_datetime(self, workdays):
        start_day = self.start_day
        if workdays == 0:
            return None

        start = 1
        while start != workdays:
            start_day += timedelta(days=1)
            if start_day.weekday() not in [5, 6]:
                start += 1
        return start_day

    def offboarding_workday_to_date(self, workdays):
        # Converts the workday (before the end date) to the actual date on which it
        # triggers. This will skip any weekends.
        base_date = self.termination_date

        while workdays > 0:
            base_date -= timedelta(days=1)
            if base_date.weekday() not in [5, 6]:
                workdays -= 1

        return base_date

    @cached_property
    def days_before_termination_date(self):
        # Checks how many workdays we are away from the employee's last day.
        # This will skip any weekends.
        date = self.get_local_time().date()

        termination_date = self.termination_date
        if termination_date < date:
            # passed the termination date
            return -1

        days = 0
        while termination_date != date:
            date += timedelta(days=1)
            if date.weekday() not in [5, 6]:
                days += 1
        return days

    @cached_property
    def days_before_starting(self):
        # not counting workdays here
        if self.start_day <= self.get_local_time().date():
            return 0
        return (self.start_day - self.get_local_time().date()).days

    def get_local_time(self, date=None):
        from organization.models import Organization

        if date is not None:
            date = date.replace(tzinfo=None)

        local_tz = pytz.timezone("UTC")
        org = Organization.object.get()
        us_tz = (
            pytz.timezone(org.timezone)
            if self.timezone == ""
            else pytz.timezone(self.timezone)
        )
        local = (
            local_tz.localize(datetime.now())
            if date is None
            else local_tz.localize(date)
        )
        return us_tz.normalize(local.astimezone(us_tz))

    def personalize(self, text, extra_values=None):
        if extra_values is None:
            extra_values = {}
        t = Template(text)
        department = ""
        manager = ""
        manager_email = ""
        buddy = ""
        buddy_email = ""
        if self.department is not None:
            department = self.department.name
        if self.manager is not None:
            manager = self.manager.full_name
            manager_email = self.manager.email
        if self.buddy is not None:
            buddy = self.buddy.full_name
            buddy_email = self.buddy.email
        new_hire_context = {
            "manager": manager,
            "buddy": buddy,
            "position": self.position,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "email": self.email,
            "start": self.start_day,
            "buddy_email": buddy_email,
            "manager_email": manager_email,
            "access_overview": lazy(self.get_access_overview, str),
            "department": department,
        }

        text = t.render(Context(new_hire_context | extra_values))
        # Remove non breakable space html code (if any). These could show up in the
        # Slack bot.
        text = text.replace("&nbsp;", " ")
        return text

    def get_access_overview(self):
        all_access = []
        for integration, access in self.check_integration_access().items():
            if access is None:
                access_str = _("(unknown)")
            elif access:
                access_str = _("(has access)")
            else:
                access_str = _("(no access)")

            all_access.append(f"{integration} {access_str}")

        return ", ".join(all_access)

    def check_integration_access(self):
        items = {}
        for integration_user in IntegrationUser.objects.filter(user=self):
            items[integration_user.integration.name] = not integration_user.revoked

        for integration in Integration.objects.filter(manifest__exists__isnull=False):
            items[integration.name] = integration.user_exists(self)

        return items

    def reset_otp_recovery_keys(self):
        self.user_otp.all().delete()
        newItems = [OTPRecoveryKey(user=self) for x in range(10)]
        OTPRecoveryKey.objects.bulk_create(newItems)
        return self.user_otp.all().values_list("key", flat=True)

    def check_otp_recovery_key(self, totp_input):
        otp_recovery_key = None
        for i in OTPRecoveryKey.objects.filter(is_used=False, user=self):
            if i.key == totp_input:
                otp_recovery_key = i
                break
        if otp_recovery_key is not None:
            otp_recovery_key.is_used = True
            otp_recovery_key.save()
        return otp_recovery_key

    @property
    def is_admin_or_manager(self):
        return self.role in [get_user_model().Role.ADMIN, get_user_model().Role.MANAGER]

    @property
    def is_admin(self):
        return self.role == get_user_model().Role.ADMIN

    @property
    def is_new_hire(self):
        return self.role == get_user_model().Role.NEWHIRE

    def __str__(self):
        return "%s" % self.full_name


class ToDoUserManager(models.Manager):
    def all_to_do(self, user):
        return super().get_queryset().filter(user=user, completed=False)

    def overdue(self, user):
        return (
            super()
            .get_queryset()
            .filter(user=user, completed=False, to_do__due_on_day__lt=user.workday)
            .exclude(to_do__due_on_day=0)
        )

    def due_today(self, user):
        return (
            super()
            .get_queryset()
            .filter(user=user, completed=False, to_do__due_on_day=user.workday)
        )


class ToDoUser(CompletedFormCheck, models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="to_do_new_hire", on_delete=models.CASCADE
    )
    to_do = models.ForeignKey(ToDo, related_name="to_do", on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    form = models.JSONField(default=list)
    reminded = models.DateTimeField(null=True)

    objects = ToDoUserManager()

    @cached_property
    def object_name(self):
        return self.to_do.name

    def mark_completed(self):
        from admin.sequences.tasks import process_condition

        self.completed = True
        self.save()

        # Get conditions with this to do item as (part of the) condition
        conditions = self.user.conditions.filter(condition_to_do=self.to_do)

        # Send answers back to slack channel?
        if self.to_do.send_back:
            blocks = [
                paragraph(
                    _("*Our new hire %(name)s just answered some questions:*")
                    % {"name": self.user.full_name}
                )
            ]
            for question in self.form:
                # For some reason, Slack adds a \n to the name, which messes up
                # formatting.
                title = question["data"]["text"].replace("\n", "")
                blocks.append(paragraph(f"*{title}*\n{question['answer']}"))

            Slack().send_message(
                blocks=blocks,
                text=(
                    _("Our new hire %(name)s just answered some questions:")
                    % {"name": self.user.full_name}
                ),
                channel=self.to_do.slack_channel.name,
            )

        for condition in conditions:
            condition_to_do_ids = condition.condition_to_do.values_list("id", flat=True)

            # Check if all to do items already have been added to new hire and are
            # completed. If not, then we know it should not be triggered yet
            to_do_user = ToDoUser.objects.filter(
                to_do__in=condition_to_do_ids, user=self.user, completed=True
            )

            # If the amount matches, then we should process it
            if to_do_user.count() == len(condition_to_do_ids):
                # Send notification only if user has a slack account
                process_condition(
                    condition.id, self.user.id, self.user.has_slack_account
                )


class PreboardingUser(CompletedFormCheck, models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="new_hire_preboarding", on_delete=models.CASCADE
    )
    preboarding = models.ForeignKey(
        Preboarding, related_name="preboarding_new_hire", on_delete=models.CASCADE
    )
    form = models.JSONField(default=list)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # Adding order number when record is not created yet (always the last item
        # in the list)
        if not self.pk:
            self.order = PreboardingUser.objects.filter(
                user=self.user, preboarding=self.preboarding
            ).count()
        super(PreboardingUser, self).save(*args, **kwargs)


class ResourceUser(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="new_hire_resource", on_delete=models.CASCADE
    )
    resource = models.ForeignKey(
        Resource, related_name="resource_new_hire", on_delete=models.CASCADE
    )
    step = models.IntegerField(default=0)
    answers = models.ManyToManyField(CourseAnswer)
    reminded = models.DateTimeField(null=True)
    completed_course = models.BooleanField(default=False)

    def add_step(self):
        self.step += 1
        self.save()

        # Check if we are already past the max amount of steps
        # Avoid race conditions
        chapters = self.resource.chapters
        if self.step > chapters.count():
            return None

        # Check if that's the last one and wrap up if so
        if self.step == chapters.count():
            self.completed_course = True
            self.save()

            # Up one for completed stat in user
            self.user.completed_tasks += 1
            self.user.save()
            return None

        # Skip over any folders
        # This is safe, as a folder can never be the last type
        while (
            chapters.filter(order=self.step).exists()
            and chapters.get(order=self.step).type == 1
        ):
            self.step += 1
            self.save()

        # Return next chapter
        return chapters.get(order=self.step)

    @property
    def object_name(self):
        return self.resource.name

    @property
    def amount_chapters_in_course(self):
        return self.resource.chapters.count()

    @cached_property
    def percentage_completed(self):
        return self.step / self.resource.chapters.count() * 100

    @property
    def is_course(self):
        # used to determine if item should show up as course or as article
        return self.resource.course and not self.completed_course

    @cached_property
    def get_rating(self):
        if not self.answers.exists():
            return "n/a"

        amount_of_questions = 0
        amount_of_correct_answers = 0
        for question_page in self.answers.all():
            amount_of_questions += len(question_page.chapter.content["blocks"])
            for idx, answer in enumerate(question_page.chapter.content["blocks"]):
                if question_page.answers[f"item-{idx}"] == answer["answer"]:
                    amount_of_correct_answers += 1
        return _(
            "%(amount_of_correct_answers)s correct answers out of "
            "%(amount_of_questions)s questions"
        ) % {
            "amount_of_correct_answers": amount_of_correct_answers,
            "amount_of_questions": amount_of_questions,
        }

    def get_user_answer_by_chapter(self, chapter):
        if not self.answers.filter(chapter=chapter).exists():
            return None
        return self.answers.get(chapter=chapter)


class NewHireWelcomeMessage(models.Model):
    # messages placed through the slack bot
    new_hire = models.ForeignKey(
        get_user_model(), related_name="welcome_new_hire", on_delete=models.CASCADE
    )
    colleague = models.ForeignKey(
        get_user_model(), related_name="welcome_colleague", on_delete=models.CASCADE
    )
    message = models.TextField()


class IntegrationUser(models.Model):
    # UserIntegration
    # logging when an integration was enabled and revoked
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    integration = models.ForeignKey(
        "integrations.Integration", on_delete=models.CASCADE
    )
    revoked = models.BooleanField(default=False)

    class Meta:
        unique_together = ["user", "integration"]


class OTPRecoveryKey(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="user_otp", on_delete=models.CASCADE
    )
    key = EncryptedTextField(default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
