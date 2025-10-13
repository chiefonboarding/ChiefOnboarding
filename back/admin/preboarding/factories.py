import factory
from factory.fuzzy import FuzzyText
from misc.mixins import DepartmentsPostGenerationMixin
from pytest_factoryboy import register

from admin.preboarding.models import Preboarding


@register
class PreboardingFactory(factory.django.DjangoModelFactory, DepartmentsPostGenerationMixin):
    name = FuzzyText()

    class Meta:
        model = Preboarding
