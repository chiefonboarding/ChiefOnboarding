import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.preboarding.models import Preboarding
from misc.factories import DepartmentsPostGenerationMixin


@register
class PreboardingFactory(
    factory.django.DjangoModelFactory, DepartmentsPostGenerationMixin
):
    name = FuzzyText()

    class Meta:
        model = Preboarding
        skip_postgeneration_save = True
