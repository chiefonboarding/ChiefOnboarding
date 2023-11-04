import factory
from django.conf import settings
from django.utils import timezone
from factory.fuzzy import FuzzyChoice, FuzzyText
from pytest_factoryboy import register

from .models import Notification, Organization, WelcomeMessage


@register
class OrganizationFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    timed_triggers_last_check = factory.LazyFunction(lambda: timezone.now().date())

    class Meta:
        model = Organization


@register
class NotificationFactory(factory.django.DjangoModelFactory):
    notification_type = FuzzyChoice([x[0] for x in Notification.Type.choices])
    extra_text = FuzzyText()

    class Meta:
        model = Notification


@register
class WelcomeMessageFactory(factory.django.DjangoModelFactory):
    message_type = FuzzyChoice([x[0] for x in WelcomeMessage.Type.choices])
    language = FuzzyChoice([x[0] for x in settings.LANGUAGES])
    message = FuzzyText()

    class Meta:
        model = WelcomeMessage
