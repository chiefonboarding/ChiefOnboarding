import uuid
from datetime import datetime, timedelta

import pyotp
import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.template import Context, Template
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from fernet_fields import EncryptedTextField

from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import CourseAnswer, Resource
from admin.sequences.models import Condition
from admin.to_do.models import ToDo
from misc.models import File
from slack_bot.utils import Slack, paragraph

ROLE_CHOICES = (
    (0, _("New Hire")),
    (1, _("Administrator")),
    (2, _("Manager")),
    (3, _("Other")),
)


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


class ManagerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role__in=[1, 2])

    def with_slack(self):
        return self.get_queryset().exclude(slack_user_id="")


class NewHireManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=0)

    def without_slack(self):
        return self.get_queryset().filter(slack_user_id="")

    def with_slack(self):
        return self.get_queryset().exclude(slack_user_id="")

    def starting_today(self):
        return self.get_queryset().filter(start_day=datetime.now().date())

    def to_introduce(self):
        return self.get_queryset().filter(
            is_introduced_to_colleagues=False, start_day__gte=datetime.now().date()
        )


class AdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=1)


class User(AbstractBaseUser):
    first_name = models.CharField(verbose_name=_("First name"), max_length=200)
    last_name = models.CharField(verbose_name=_("Last name"), max_length=200)
    email = models.EmailField(verbose_name=_("Email"), max_length=200, unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
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
    timezone = models.CharField(verbose_name=_("Timezone"), default="", max_length=1000)
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
        choices=ROLE_CHOICES,
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
    unique_url = models.CharField(max_length=250, null=True, unique=True, blank=True)

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

    # Conditions copied over from chosen sequences
    conditions = models.ManyToManyField(Condition)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()
    managers_and_admins = ManagerManager()
    new_hires = NewHireManager()
    admins = AdminManager()
    ordering = ("first_name",)

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
        last_notification = self.notification_receivers.last()
        if last_notification is not None:
            return last_notification.created > self.seen_updates
        return False

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

        start = 1
        while start != workdays:
            start_day += timedelta(days=1)
            if start_day.weekday() not in [5, 6]:
                start += 1
        return start_day

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

    def personalize(self, text, extra_values={}):
        t = Template(text)
        manager = ""
        manager_email = ""
        buddy = ""
        buddy_email = ""
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
        }
        text = t.render(Context(new_hire_context | extra_values))
        return text

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
        return self.role in (1, 2)

    @property
    def is_admin(self):
        return self.role == 1

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


class ToDoUser(models.Model):
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

    @property
    def completed_form_items(self):
        completed_blocks = []
        filled_items = [item["id"] for item in self.form]

        for block in self.to_do.content["blocks"]:
            if (
                "data" in block
                and "type" in block["data"]
                and block["data"]["type"] in ["input", "text", "check", "upload"]
            ):
                item = next((x for x in filled_items if x == block["id"]), None)
                if item is not None:
                    completed_blocks.append(item)

        return completed_blocks

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
                process_condition(condition.id, self.user.id, self.user.has_slack_account)


class PreboardingUser(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="new_hire_preboarding", on_delete=models.CASCADE
    )
    preboarding = models.ForeignKey(
        Preboarding, related_name="preboarding_new_hire", on_delete=models.CASCADE
    )
    form = models.JSONField(default=list)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    @property
    def completed_form_items(self):
        completed_blocks = []
        filled_items = [item["id"] for item in self.form]

        for block in self.preboarding.content["blocks"]:
            if (
                "data" in block
                and "type" in block["data"]
                and block["data"]["type"] in ["input", "text", "check", "upload"]
            ):
                item = next((x for x in filled_items if x == block["id"]), None)
                if item is not None:
                    completed_blocks.append(item)

        return completed_blocks

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

    @property
    def percentage_completed(self):
        return self.step / self.resource.chapters.count() * 100

    @property
    def is_course(self):
        # used to determine if item should show up as course or as article
        return self.resource.course and not self.completed_course

    @property
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


class OTPRecoveryKey(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="user_otp", on_delete=models.CASCADE
    )
    key = EncryptedTextField(default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
