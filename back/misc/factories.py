import factory
from factory.fuzzy import FuzzyText

from .models import File


class FileFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()
    key = FuzzyText()
    ext = "png"

    class Meta:
        model = File


class DepartmentsPostGenerationMixin(factory.Factory):
    @factory.post_generation
    def departments(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.departments.set(extracted)
