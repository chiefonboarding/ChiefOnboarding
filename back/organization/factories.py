import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from .models import Organization


@register
class OrganizationFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Organization
