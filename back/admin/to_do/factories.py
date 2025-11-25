import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.to_do.models import ToDo
from misc.factories import DepartmentsPostGenerationMixin


@register
class ToDoFactory(DepartmentsPostGenerationMixin, factory.django.DjangoModelFactory):
    name = FuzzyText()
    due_on_day = 0
    content = {
        "time": 0,
        "blocks": [
            {"data": {"text": "Please complete this item!"}, "type": "paragraph"}
        ],
    }

    class Meta:
        model = ToDo
        skip_postgeneration_save = True
