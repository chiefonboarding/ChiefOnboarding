import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.badges.models import Badge


@register
class BadgeFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Badge
