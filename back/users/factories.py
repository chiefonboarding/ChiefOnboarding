import datetime

import factory
from django.contrib.auth import get_user_model
from factory.fuzzy import FuzzyText

from admin.integrations.factories import ManualUserProvisionIntegrationFactory
from admin.preboarding.factories import PreboardingFactory
from admin.resources.factories import ResourceFactory
from admin.to_do.factories import ToDoFactory

from .models import (
    Department,
    IntegrationUser,
    NewHireWelcomeMessage,
    PreboardingUser,
    ResourceUser,
    ToDoUser,
    User,
)


class BaseUserFactory(factory.django.DjangoModelFactory):
    first_name = FuzzyText()
    last_name = FuzzyText()

    class Meta:
        model = User
        skip_postgeneration_save = True

    @factory.post_generation
    def departments(obj, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            obj.departments.set(extracted)


class DepartmentFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Department


class NewHireFactory(BaseUserFactory):
    role = get_user_model().Role.NEWHIRE
    start_day = factory.LazyFunction(lambda: datetime.datetime.now().date())
    email = factory.Sequence(lambda n: "fake_new_hire_{}@example.com".format(n))


class AdminFactory(BaseUserFactory):
    role = get_user_model().Role.ADMIN
    email = factory.Sequence(lambda n: "fake_admin_{}@example.com".format(n))


class ManagerFactory(BaseUserFactory):
    role = get_user_model().Role.MANAGER
    email = factory.Sequence(lambda n: "fake_manager_{}@example.com".format(n))


class EmployeeFactory(BaseUserFactory):
    is_active = False
    role = get_user_model().Role.OTHER
    message = "Hi {{ first_name }}, how is it going? Great to have you with us!"
    position = "CEO"
    email = factory.Sequence(lambda n: "fake_employee_{}@example.com".format(n))


class NewHireWelcomeMessageFactory(factory.django.DjangoModelFactory):
    message = FuzzyText()
    new_hire = factory.SubFactory(NewHireFactory)
    colleague = factory.SubFactory(EmployeeFactory)

    class Meta:
        model = NewHireWelcomeMessage


class ToDoUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    to_do = factory.SubFactory(ToDoFactory)

    class Meta:
        model = ToDoUser


class ResourceUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    resource = factory.SubFactory(ResourceFactory)

    class Meta:
        model = ResourceUser


class PreboardingUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    preboarding = factory.SubFactory(PreboardingFactory)

    class Meta:
        model = PreboardingUser


class IntegrationUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(NewHireFactory)
    integration = factory.SubFactory(ManualUserProvisionIntegrationFactory)

    class Meta:
        model = IntegrationUser
