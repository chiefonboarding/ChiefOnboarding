import factory
from factory.fuzzy import FuzzyText
from pytest_factoryboy import register

from admin.appointments.models import Appointment


@register
class AppointmentFactory(factory.django.DjangoModelFactory):
    name = FuzzyText()

    class Meta:
        model = Appointment
