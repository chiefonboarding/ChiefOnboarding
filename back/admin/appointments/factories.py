import factory
from factory.fuzzy import FuzzyText
from misc.mixins import DepartmentsPostGenerationMixin
from pytest_factoryboy import register

from admin.appointments.models import Appointment


@register
class AppointmentFactory(factory.django.DjangoModelFactory, DepartmentsPostGenerationMixin):
    name = FuzzyText()

    class Meta:
        model = Appointment
