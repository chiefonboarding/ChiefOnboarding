from __future__ import unicode_literals

import pytz
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)
from datetime import datetime

from django.db.models import Q
from django.template import Template, Context
from django.utils.crypto import get_random_string

from resources.models import Resource
from appointments.models import Appointment
from to_do.models import ToDo
from preboarding.models import Preboarding
from badges.models import Badge
from misc.models import File

from resources.models import CourseAnswer
from sequences.models import Condition

from introductions.models import Introduction
from datetime import date, timedelta
import uuid
import pyotp
from fernet_fields import EncryptedTextField

LANGUAGE_CHOICES = (
    ('en', 'English'),
    ('nl', 'Dutch'),
    ('fr', 'French'),
    ('de', 'German'),
    ('tr', 'Turkish'),
    ('pt', 'Portuguese'),
    ('es', 'Spanish')
)

ROLE_CHOICES = (
    (0, 'New Hire'),
    (1, 'Admin'),
    (2, 'Manager'),
    (3, 'Other')
)


class CustomUserManager(BaseUserManager):

    def _create_user(self, first_name, last_name, email, password, role, **extra_fields):
        now = datetime.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(first_name=first_name, last_name=last_name, email=email, role=role,
                          date_joined=now, **extra_fields)
        if password is not None:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_new_hire(self, first_name, last_name, email, password=None, **extra_fields):
        user = self._create_user(first_name, last_name, email, password, 0, **extra_fields)
        return user

    def create_admin(self, first_name, last_name, email, password, **extra_fields):
        return self._create_user(first_name, last_name, email, password, 1, **extra_fields)

    def create_manager(self, first_name, last_name, email, password, **extra_fields):
        return self._create_user(first_name, last_name, email, password, 2, **extra_fields)


class ManagerManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=2)


class NewHireManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=0)


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
    position = models.CharField(max_length=300, null=True, blank=True)
    phone = models.CharField(max_length=300, null=True, blank=True)
    slack_user_id = models.CharField(max_length=100, null=True, blank=True)
    slack_channel_id = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField(default='', blank=True)
    profile_image = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    linkedin = models.CharField(default='', max_length=100, blank=True)
    facebook = models.CharField(default='', max_length=100, blank=True)
    twitter = models.CharField(default='', max_length=100, blank=True)
    timezone = models.CharField(default='', max_length=1000)
    department = models.TextField(default='', blank=True)
    language = models.CharField(default='en', choices=LANGUAGE_CHOICES, max_length=5)
    role = models.IntegerField(choices=ROLE_CHOICES, default=3)
    is_active = models.BooleanField(default=True)
    is_introduced_to_colleagues = models.BooleanField(default=False)
    sent_preboarding_details = models.BooleanField(default=False)
    resources = models.ManyToManyField(Resource, through='ResourceUser')
    totp_secret = EncryptedTextField(blank=True)
    requires_otp = models.BooleanField(default=False)
    # new hire specific
    completed_tasks = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)
    buddy = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='new_hire_buddy')
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, related_name='new_hire_manager')
    seen_updates = models.DateField(auto_now_add=True)
    start_day = models.DateField(null=True, blank=True, help_text="First working day")
    unique_url = models.CharField(max_length=250, null=True, unique=True, blank=True)
    to_do = models.ManyToManyField(ToDo, through='ToDoUser')
    introductions = models.ManyToManyField(Introduction)
    appointments = models.ManyToManyField(Appointment)
    conditions = models.ManyToManyField(Condition)
    preboarding = models.ManyToManyField(Preboarding, through='PreboardingUser')
    badges = models.ManyToManyField(Badge)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()
    managers = ManagerManager()
    new_hires = NewHireManager()
    admins = AdminManager()
    ordering = ('first_name',)

    def full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

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

    def workday(self):
        if self.start_day > date.today():
            return 0
        start_day = self.start_day
        amount_of_workdays = 1
        while date.today() != start_day:
            start_day += timedelta(days=1)
            if start_day.weekday() != 5 and start_day.weekday() != 6:
                amount_of_workdays += 1
        return amount_of_workdays

    def days_before_starting(self):
        # not counting workdays here
        if self.start_day <= date.today():
            return 0
        return (self.start_day - date.today()).days

    def get_local_time(self, date=None):
        from organization.models import Organization
        local_tz = pytz.timezone("UTC")
        org = Organization.object.get()
        us_tz = pytz.timezone(
            org.timezone) if self.timezone == "" else pytz.timezone(self.timezone)
        local = local_tz.localize(
            datetime.now()) if date is None else local_tz.localize(date)
        return us_tz.normalize(local.astimezone(us_tz))

    def personalize(self, text):
        t = Template(text)
        manager = ''
        buddy = ''
        if self.manager is not None:
            manager = self.manager.full_name()
        if self.buddy is not None:
            buddy = self.buddy.full_name()
        text = t.render(Context(
            {'manager': manager, 'buddy': buddy, 'position': self.position, 'last_name': self.last_name,
             'first_name': self.first_name, 'email': self.email}))
        return text

    def reset_otp_keys(self):
        OTPRecoveryKey.objects.filter(user=self).delete()
        newItems = [OTPRecoveryKey(user=self) for x in range(10)]
        objs = OTPRecoveryKey.objects.bulk_create(newItems)
        return objs

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

    def __str__(self):
        return u'%s' % self.full_name()


class ToDoUser(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='to_do_new_hire', on_delete=models.CASCADE)
    to_do = models.ForeignKey(ToDo, related_name='to_do', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    form = models.JSONField(models.TextField(default='[]'), default=list)
    reminded = models.DateTimeField(null=True)

    def mark_completed(self):
        self.completed = True
        self.save()
        items_added = {
            'to_do': [],
            'resources': [],
            'badges': [],
            'introductions': []
        }
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
                items_added['to_do'].extend(new_items['to_do'])
                items_added['resources'].extend(new_items['resources'])
                items_added['badges'].extend(new_items['badges'])
                items_added['introductions'].extend(new_items['introductions'])

        return items_added


class PreboardingUser(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='new_hire_preboarding', on_delete=models.CASCADE)
    preboarding = models.ForeignKey(Preboarding, related_name='preboarding_new_hire', on_delete=models.CASCADE)
    form = models.JSONField(models.TextField(max_length=100000, default='[]'), default=list)
    completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        # adding order number when record is not created yet (always the last item in the list)
        if not self.pk:
            self.order = PreboardingUser.objects.filter(user=self.user, preboarding=self.preboarding).count()
        super(PreboardingUser, self).save(*args, **kwargs)


class ResourceUser(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='new_hire_resource', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, related_name='resource_new_hire', on_delete=models.CASCADE)
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

    def is_course(self):
        return self.resource.course and self.resource.chapters.count() is not self.step - 1


class NewHireWelcomeMessage(models.Model):
    # messages placed through the slack bot
    new_hire = models.ForeignKey(get_user_model(), related_name='welcome_new_hire', on_delete=models.CASCADE)
    colleague = models.ForeignKey(get_user_model(), related_name='welcome_colleague', on_delete=models.CASCADE)
    message = models.TextField()


class OTPRecoveryKey(models.Model):
    user = models.ForeignKey(get_user_model(), related_name='user_otp', on_delete=models.CASCADE)
    key = EncryptedTextField(default=uuid.uuid4)
    is_used = models.BooleanField(default=False)
    

