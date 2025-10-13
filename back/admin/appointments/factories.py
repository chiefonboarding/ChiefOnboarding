import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.appointments.models import Appointment
from misc.mixins import DepartmentsPostGenerationMixin


@register
class AppointmentFactory(
    factory.django.DjangoModelFactory, DepartmentsPostGenerationMixin
):
    name = FuzzyText()

    class Meta:
        model = Appointment
