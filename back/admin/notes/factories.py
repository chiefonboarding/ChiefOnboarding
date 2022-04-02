import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.notes.models import Note
from users.factories import AdminFactory, NewHireFactory


@register
class NoteFactory(factory.django.DjangoModelFactory):
    content = FuzzyText()
    admin = factory.SubFactory(AdminFactory)
    new_hire = factory.SubFactory(NewHireFactory)

    class Meta:
        model = Note
