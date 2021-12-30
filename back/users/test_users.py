import pytest
from freezegun import freeze_time
import datetime

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
    assert manager.role == 2
    assert employee.role == 3

    assert User.objects.count() == 4
    assert User.new_hires.count() == 1
    assert User.admins.count() == 2
    assert User.managers.count() == 1

    assert admin.is_admin_or_manager
    assert manager.is_admin_or_manager
    assert not new_hire.is_admin_or_manager
    assert not employee.is_admin_or_manager

@pytest.mark.django_db
def test_workday(new_hire_factory):
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(start_day=datetime.datetime.today().date())
    freezer.stop()

    # Freeze on the Monday
    freezer = freeze_time("2021-01-11")
    freezer.start()
    assert user.workday() == 0
    freezer.stop()

    # First day
    freezer = freeze_time("2021-01-12")
    freezer.start()
    assert user.workday() == 1
    freezer.stop()

    # Second day
    freezer = freeze_time("2021-01-13")
    freezer.start()
    assert user.workday() == 2
    freezer.stop()

    # Crossing weekend
    freezer = freeze_time("2021-01-18")
    freezer.start()
    assert user.workday() == 5
    freezer.stop()


@pytest.mark.django_db
def test_days_before_starting(new_hire_factory):
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(start_day=datetime.datetime.today().date())
    freezer.stop()

    # Freeze on the Monday
    freezer = freeze_time("2021-01-11")
    freezer.start()
    assert user.days_before_starting() == 1
    freezer.stop()

    # 4 days before user starts (including weekend)
    freezer = freeze_time("2021-01-08")
    freezer.start()
    assert user.days_before_starting() == 4
    freezer.stop()

    # Once new hire has started
    freezer = freeze_time("2021-01-13")
    freezer.start()
    assert user.days_before_starting() == 0
    freezer.stop()


@pytest.mark.django_db
def test_personalize(manager_factory, new_hire_factory):
    manager = manager_factory(first_name="jane", last_name="smith")
    new_hire = new_hire_factory(first_name="john", last_name="smith", manager=manager, position="developer")

    text = 'Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and you will be our {{ position }}'
    text_without_spaces = 'Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you will be our {{position}}'

    expected_output = 'Hello john smith, your manager is jane smith and you will be our developer'

    assert new_hire.personalize(text) == expected_output
    assert new_hire.personalize(text_without_spaces) == expected_output

# @pytest.mark.django_db
# def test_resource_user(resource):
#     user = User.objects.create_new_hire('john', 'smith', 'john@example.com', 'johnpassword')
#     resource_user = ResourceUser.objects.create(user=user, resource=resource)

#     resource_user.add_step(resource.chapters.first())

#     assert resource_user.completed_course == False
#     assert resource_user.step == 0
#     assert resource_user.is_course() == True

#     resource_user.add_step(resource.chapters.all()[1])

#     # completed course
#     assert resource_user.completed_course == True
#     assert resource_user.step == 1
#     assert resource_user.is_course() == False
