import factory
from pytest_factoryboy import register

from .models import User


@register
class NewHireFactory(factory.django.DjangoModelFactory):
    role = 0
    email = factory.Sequence(lambda n: 'fake_new_hire_{}@example.com'.format(n))

    class Meta:
        model = User


@register
class AdminFactory(factory.django.DjangoModelFactory):
    role = 1
    email = factory.Sequence(lambda n: 'fake_admin_{}@example.com'.format(n))

    class Meta:
        model = User


@register
class ManagerFactory(factory.django.DjangoModelFactory):
    role = 2
    email = factory.Sequence(lambda n: 'fake_manager_{}@example.com'.format(n))

    class Meta:
        model = User


@register
class EmployeeFactory(factory.django.DjangoModelFactory):
    role = 3
    email = factory.Sequence(lambda n: 'fake_employee_{}@example.com'.format(n))

    class Meta:
        model = User

