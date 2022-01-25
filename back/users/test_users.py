import datetime

import pytest
from freezegun import freeze_time

from .factories import *
from .models import User


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
@pytest.mark.parametrize(
    "date, workday",
    [
        ("2021-01-11", 0),
        ("2021-01-12", 1),
        ("2021-01-13", 2),
        ("2021-01-18", 5),
    ],
)
def test_workday(date, workday, new_hire_factory):
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(start_day=datetime.datetime.today().date())
    freezer.stop()

    freezer = freeze_time(date)
    freezer.start()
    assert user.workday() == workday
    freezer.stop()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "date, daybefore",
    [
        ("2021-01-11", 1),
        ("2021-01-08", 4),
        ("2021-01-13", 0),
    ],
)
def test_days_before_starting(date, daybefore, new_hire_factory):
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(start_day=datetime.datetime.today().date())
    freezer.stop()

    freezer = freeze_time(date)
    freezer.start()
    assert user.days_before_starting() == daybefore
    freezer.stop()


@pytest.mark.django_db
def test_personalize(manager_factory, new_hire_factory):
    manager = manager_factory(first_name="jane", last_name="smith")
    new_hire = new_hire_factory(
        first_name="john", last_name="smith", manager=manager, position="developer"
    )

    text = "Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and you will be our {{ position }}"
    text_without_spaces = "Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you will be our {{position}}"

    expected_output = (
        "Hello john smith, your manager is jane smith and you will be our developer"
    )

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
