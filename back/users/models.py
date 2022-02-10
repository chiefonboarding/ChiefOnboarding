import uuid
from datetime import date, datetime, timedelta

import pyotp
import pytz
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.template import Context, Template
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from fernet_fields import EncryptedTextField

from admin.appointments.models import Appointment
from admin.badges.models import Badge
from admin.introductions.models import Introduction
from admin.preboarding.models import Preboarding
from admin.resources.models import CourseAnswer, Resource
from admin.sequences.models import Condition
from admin.to_do.models import ToDo
from misc.models import File
from organization.models import Changelog

LANGUAGE_CHOICES = (
    ("en", "English"),
    ("nl", "Dutch"),
    ("fr", "French"),
    ("de", "German"),
    ("tr", "Turkish"),
    ("pt", "Portuguese"),
    ("es", "Spanish"),
)

ROLE_CHOICES = ((0, "New Hire"), (1, "Administrator"), (2, "Manager"), (3, "Other"))


class Department(models.Model):
    """
    Department that has been attached to a user
    At the moment, only one department per user
    """
    name = models.TextField()

    def __str__(self):
        return "%s" % self.name


class CustomUserManager(BaseUserManager):
    def _create_user(
        self, first_name, last_name, email, password, role, **extra_fields
    ):
        now = datetime.now()
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            date_joined=now,
            **extra_fields,
        )
        if password is not None:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_new_hire(
        self, first_name, last_name, email, password=None, **extra_fields
    ):
        user = self._create_user(
            first_name, last_name, email, password, 0, **extra_fields
        )
        return user

    def create_admin(self, first_name, last_name, email, password, **extra_fields):
        return self._create_user(
            first_name, last_name, email, password, 1, **extra_fields
        )

    def create_manager(self, first_name, last_name, email, password, **extra_fields):
        return self._create_user(
            first_name, last_name, email, password, 2, **extra_fields
        )

    def get_by_natural_key(self, email):
        return self.get(**{self.model.USERNAME_FIELD + "__iexact": email})


class ManagerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=2)


class NewHireManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=0)

    def without_slack(self):
        return self.get_queryset().filter(slack_user_id="")


class AdminManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(Q(role=1) | Q(role=2))


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200, unique=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    position = models.CharField(max_length=300, default="", blank=True)
    phone = models.CharField(max_length=300, default="", blank=True)
    slack_user_id = models.CharField(max_length=100, default="", blank=True)
    slack_channel_id = models.CharField(max_length=100, default="", blank=True)
    message = models.TextField(default="", blank=True)
    profile_image = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    linkedin = models.CharField(default="", max_length=100, blank=True)
    facebook = models.CharField(default="", max_length=100, blank=True)
    twitter = models.CharField(default="", max_length=100, blank=True)
    timezone = models.CharField(default="", max_length=1000)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    language = models.CharField(default="en", choices=LANGUAGE_CHOICES, max_length=5)
    role = models.IntegerField(
        choices=ROLE_CHOICES,
        default=3,
        help_text="An administrator has access to everything. A manager has only access to their new hires and their tasks.",
    )
    is_active = models.BooleanField(default=True)
    is_introduced_to_colleagues = models.BooleanField(default=False)
    sent_preboarding_details = models.BooleanField(default=False)
    totp_secret = EncryptedTextField(blank=True)
    requires_otp = models.BooleanField(default=False)
    seen_updates = models.DateField(auto_now_add=True)
    # new hire specific
    completed_tasks = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    buddy = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="new_hire_buddy"
    )
    manager = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, related_name="new_hire_manager"
    )
    start_day = models.DateField(null=True, blank=True, help_text="First working day")
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
    managers = ManagerManager()
    new_hires = NewHireManager()
    admins = AdminManager()
    ordering = ("first_name",)

    @cached_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @cached_property
    def initials(self):
        initial_characters = ""
        if len(self.first_name):
            initial_characters += self.first_name[0]
        if len(self.last_name):
            initial_characters += self.last_name[0]
        return initial_characters

    @cached_property
    def has_password(self):
        return self.password == ""

    @cached_property
    def progress(self):
        return self.total_tasks - self.completed_tasks

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

    def workday(self):
        start_day = self.start_day
        if start_day > self.get_local_time().date():
            return 0
        amount_of_workdays = 1
        while self.get_local_time().date() != start_day:
            start_day += timedelta(days=1)
            if start_day.weekday() != 5 and start_day.weekday() != 6:
                amount_of_workdays += 1
        return amount_of_workdays

    def days_before_starting(self):
        # not counting workdays here
        if self.start_day <= self.get_local_time().date():
            return 0
        return (self.start_day - self.get_local_time().date()).days

    def get_local_time(self, date=None):
        from organization.models import Organization

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

    def personalize(self, text):
        t = Template(text)
        manager = ""
        buddy = ""
        if self.manager is not None:
            manager = self.manager.full_name
        if self.buddy is not None:
            buddy = self.buddy.full_name
        text = t.render(
            Context(
                {
                    "manager": manager,
                    "buddy": buddy,
                    "position": self.position,
                    "last_name": self.last_name,
                    "first_name": self.first_name,
                    "email": self.email,
                }
            )
        )
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

    @property
    def has_new_changelog_notifications(self):
        last_changelog_item = Changelog.objects.last()
        if last_changelog_item is not None:
            return self.seen_updates < last_changelog_item.added
        return False

    def __str__(self):
        return "%s" % self.full_name




class ToDoUser(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="to_do_new_hire", on_delete=models.CASCADE
    )
    to_do = models.ForeignKey(ToDo, related_name="to_do", on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    form = models.JSONField(models.TextField(default="[]"), default=list)
    reminded = models.DateTimeField(null=True)

    def mark_completed(self):
        self.completed = True
        self.save()
        items_added = {"to_do": [], "resources": [], "badges": [], "introductions": []}
        conditions = self.user.conditions.filter(condition_to_do=self.to_do)
        for i in conditions:
            # check if all conditions are met
            valid = True
            for j in i.condition_to_do.all():
                to_do_user = ToDoUser.objects.filter(to_do=j, user=self.user)
                if not to_do_user.exists() or not to_do_user.first().completed:
                    valid = False
            if valid:
                new_items = i.process_condition(self.user)
                items_added["to_do"].extend(new_items["to_do"])
                items_added["resources"].extend(new_items["resources"])
                items_added["badges"].extend(new_items["badges"])
                items_added["introductions"].extend(new_items["introductions"])

        return items_added


class PreboardingUser(models.Model):
    user = models.ForeignKey(
        get_user_model(), related_name="new_hire_preboarding", on_delete=models.CASCADE
    )
    preboarding = models.ForeignKey(
        Preboarding, related_name="preboarding_new_hire", on_delete=models.CASCADE
    )
    form = models.JSONField(
        models.TextField(max_length=100000, default="[]"), default=list
    )
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # adding order number when record is not created yet (always the last item in the list)
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

    def add_step(self, resource_id):
        if resource_id is None:
            self.completed_course = True
            self.save()
            return
        for idx, i in enumerate(self.resource.chapters.all()):
            if i.id == resource_id.id:
                if self.resource.chapters.count() == idx + 1:
                    self.completed_course = True
                self.step = idx
                self.save()
                break

    @property
    def amount_chapters_in_course(self):
        return self.resource.chapters.count()

    @property
    def is_course(self):
        # used to determine if item should show up as course or as article
        return (
            self.resource.course and self.amount_chapters_in_course is not self.step - 1
        )


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
