import pytest

from .models import User

from .factories import *

@pytest.mark.django_db
def test_user_create(new_hire_factory, admin_factory, employee_factory, manager_factory):
    new_hire = new_hire_factory()
    admin = admin_factory()
    employee = employee_factory()
    manager = manager_factory()

    assert new_hire.role == 0
    assert admin.role == 1
    assert employee.role == 3
    assert manager.role == 2

    assert User.objects.count() == 4
    assert User.new_hires.count() == 1
    assert User.admins.count() == 2
    assert User.managers.count() == 1

    assert admin.is_admin_or_manager
    assert manager.is_admin_or_manager
    assert not new_hire.is_admin_or_manager
    assert not employee.is_admin_or_manager

