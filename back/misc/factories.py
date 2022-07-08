import factory
from factory.fuzzy import FuzzyText

from .models import File


class FileFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    key = FuzzyText()
    ext = "png"

    class Meta:
        model = File
