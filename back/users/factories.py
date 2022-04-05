import datetime

import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.resources.factories import ResourceFactory
from admin.to_do.factories import ToDoFactory

from .models import NewHireWelcomeMessage, OTPRecoveryKey, ResourceUser, ToDoUser, User


@register
class NewHireFactory(factory.django.DjangoModelFactory):
    first_name = FuzzyText()
    last_name = FuzzyText()
    role = 0
    start_day = datetime.datetime.now().date()
    email = factory.Sequence(lambda n: "fake_new_hire_{}@example.com".format(n))

    class Meta:
        model = User


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
    message = "Hi {{ first_name }}, how is it going? Great to have you with us!"
    position = "CEO"
    email = factory.Sequence(lambda n: "fake_employee_{}@example.com".format(n))

    class Meta:
        model = User


@register
class OTPRecoveryKeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OTPRecoveryKey


@register
class NewHireWelcomeMessageFactory(factory.django.DjangoModelFactory):
    message = FuzzyText()
    new_hire = factory.SubFactory(NewHireFactory)
    colleague = factory.SubFactory(EmployeeFactory)

    class Meta:
        model = NewHireWelcomeMessage


@register
class ToDoUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    to_do = factory.SubFactory(ToDoFactory)

    class Meta:
        model = ToDoUser


@register
class ResourceUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    resource = factory.SubFactory(ResourceFactory)

    class Meta:
        model = ResourceUser
