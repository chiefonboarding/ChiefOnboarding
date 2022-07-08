import factory
from factory.fuzzy import FuzzyInteger, FuzzyText

from admin.appointments.factories import AppointmentFactory
from admin.badges.factories import BadgeFactory
from admin.integrations.factories import CustomIntegrationFactory
from admin.introductions.factories import IntroductionFactory
from admin.preboarding.factories import PreboardingFactory
from admin.resources.factories import ResourceFactory
from admin.to_do.factories import ToDoFactory
from users.factories import AdminFactory, EmployeeFactory

from .models import (
    Condition,
    IntegrationConfig,
    PendingAdminTask,
    PendingEmailMessage,
    PendingSlackMessage,
    PendingTextMessage,
    Sequence,
)


class PendingAdminTaskFactory(factory.django.DjangoModelFactory):
    assigned_to = factory.SubFactory(AdminFactory)
    slack_user = factory.SubFactory(EmployeeFactory)

    class Meta:
        model = PendingAdminTask


class PendingEmailMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PendingEmailMessage


class PendingSlackMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PendingSlackMessage


class PendingTextMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PendingTextMessage


class ConditionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Condition


class ConditionWithItemsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Condition

    @factory.post_generation
    def condition_to_do(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.condition_to_do.add(ToDoFactory())

    @factory.post_generation
    def to_do(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.to_do.add(ToDoFactory())

    @factory.post_generation
    def resources(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.resources.add(ResourceFactory())

    @factory.post_generation
    def appointments(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.appointments.add(AppointmentFactory())

    @factory.post_generation
    def introductions(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.introductions.add(IntroductionFactory())

    @factory.post_generation
    def preboarding(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.preboarding.add(PreboardingFactory())

    @factory.post_generation
    def badges(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.badges.add(BadgeFactory())

    @factory.post_generation
    def admin_tasks(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.admin_tasks.add(PendingAdminTaskFactory())

    @factory.post_generation
    def external_messages(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            pending_message = PendingEmailMessage()
            pending_message.save()
            obj.external_messages.add(pending_message)

    @factory.post_generation
    def integration_configs(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.integration_configs.add(IntegrationConfigFactory())


class ConditionToDoFactory(factory.django.DjangoModelFactory):
    condition_type = 1

    class Meta:
        model = Condition

    @factory.post_generation
    def condition_to_do(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Add one to do item for the condition
            obj.condition_to_do.add(ToDoFactory())


class ConditionTimedFactory(factory.django.DjangoModelFactory):
    condition_type = 0
    time = "10:00"
    days = FuzzyInteger(1, 60)

    class Meta:
        model = Condition


class SequenceFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Sequence

    @factory.post_generation
    def conditions(obj, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            # Always create the non-condition condition
            ConditionFactory(condition_type=3, sequence=obj)


class IntegrationConfigFactory(factory.django.DjangoModelFactory):
    integration = factory.SubFactory(CustomIntegrationFactory)

    class Meta:
        model = IntegrationConfig
