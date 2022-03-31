import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.preboarding.models import Preboarding


@register
class PreboardingFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Preboarding
