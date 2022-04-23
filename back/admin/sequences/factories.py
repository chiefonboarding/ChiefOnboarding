import factory
from factory.fuzzy import FuzzyInteger, FuzzyText

from admin.to_do.factories import ToDoFactory
from users.factories import AdminFactory

from .models import (
    Condition,
    PendingAdminTask,
    PendingEmailMessage,
    PendingSlackMessage,
    PendingTextMessage,
    Sequence,
)


class PendingAdminTaskFactory(factory.django.DjangoModelFactory):
    assigned_to = factory.SubFactory(AdminFactory)

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
