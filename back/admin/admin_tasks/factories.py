import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from users.factories import EmployeeFactory, NewHireFactory

from .models import AdminTask


@register
class AdminTaskFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    option = 0
    new_hire = factory.SubFactory(NewHireFactory)
    assigned_to = factory.SubFactory(EmployeeFactory)

    class Meta:
        model = AdminTask
