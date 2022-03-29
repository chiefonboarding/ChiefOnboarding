import datetime

import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from organization.factories import OrganizationFactory
from organization.models import Organization

from .models import OTPRecoveryKey, User


@register
class NewHireFactory(factory.django.DjangoModelFactory):
    first_name = FuzzyText()
    last_name = FuzzyText()
    role = 0
    email = factory.Sequence(lambda n: "fake_new_hire_{}@example.com".format(n))

    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if not Organization.objects.exists():
            OrganizationFactory()

        user = model_class(*args, **kwargs)
        user.start_day = datetime.datetime.now().date()
        user.save()
        return user


@register
class AdminFactory(factory.django.DjangoModelFactory):
    role = 1
    first_name = FuzzyText()
    last_name = FuzzyText()
    email = factory.Sequence(lambda n: "fake_admin_{}@example.com".format(n))

    class Meta:
        model = User


@register
class ManagerFactory(factory.django.DjangoModelFactory):
    first_name = FuzzyText()
    last_name = FuzzyText()
    role = 2
    email = factory.Sequence(lambda n: "fake_manager_{}@example.com".format(n))

    class Meta:
        model = User


@register
class EmployeeFactory(factory.django.DjangoModelFactory):
    first_name = FuzzyText()
    last_name = FuzzyText()
    role = 3
    email = factory.Sequence(lambda n: "fake_employee_{}@example.com".format(n))

    class Meta:
        model = User


@register
class OTPRecoveryKeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OTPRecoveryKey
