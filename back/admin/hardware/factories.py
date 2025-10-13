import factory
from factory.fuzzy import FuzzyText
from misc.mixins import DepartmentsPostGenerationMixin
from pytest_factoryboy import register

from admin.hardware.models import Hardware


@register
class HardwareFactory(factory.django.DjangoModelFactory, DepartmentsPostGenerationMixin):
    name = FuzzyText()
    content = {
        "time": 0,
        "blocks": [
            {
                "data": {"text": "Should be returned when they get terminated"},
                "type": "paragraph",
            }
        ],
    }

    class Meta:
        model = Hardware
