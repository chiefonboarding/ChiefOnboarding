import datetime

import pytest
from freezegun import freeze_time

from .factories import *  # noqa
from .models import OTPRecoveryKey, User


@pytest.mark.django_db
def test_user_create(
    new_hire_factory, admin_factory, employee_factory, manager_factory
):
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
    assert admin.is_admin
    assert manager.is_admin_or_manager
    assert not manager.is_admin
    assert not new_hire.is_admin
    assert not employee.is_admin
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
    assert user.workday == workday
    freezer.stop()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_name, last_name, initials, full_name",
    [
        ("", "Smith", "S", "Smith"),
        ("John", "Smith", "JS", "John Smith"),
        ("Zoe", "Tender", "ZT", "Zoe Tender"),
        ("", "", "", ""),
    ],
)
def test_name(first_name, last_name, initials, full_name, new_hire_factory):
    user = new_hire_factory(first_name=first_name, last_name=last_name)
    assert user.initials == initials
    assert user.full_name == full_name


@pytest.mark.django_db
def test_unique_user_props(new_hire_factory):
    user1 = new_hire_factory()
    user2 = new_hire_factory()
    assert user1.totp_secret != user2.totp_secret
    assert user1.unique_url != user2.unique_url


@pytest.mark.django_db
def test_generating_and_validating_otp_keys(new_hire_factory):
    user1 = new_hire_factory()
    user2 = new_hire_factory()

    user1_new_keys = user1.reset_otp_recovery_keys()
    user2_new_keys = user2.reset_otp_recovery_keys()

    # We cannot search through an encrypted field, so we have to loop through it
    recovery_key = None
    for item in OTPRecoveryKey.objects.all():
        if item.key == user1_new_keys[0]:
            recovery_key = item

    assert recovery_key is not None
    # Generate new keys and check that there are 10 items available and returned
    assert len(user1_new_keys) == 10
    assert OTPRecoveryKey.objects.count() == 20

    # Check wrong keys
    assert user1.check_otp_recovery_key("12324") is None
    assert user1.check_otp_recovery_key(user2_new_keys[0]) is None

    # Check correct key
    assert not recovery_key.is_used
    assert user1.check_otp_recovery_key(user1_new_keys[0]) is not None

    recovery_key.refresh_from_db()

    # Key has been used and set to used
    assert recovery_key.is_used

    # Key cannot be reused
    assert user1.check_otp_recovery_key(user1_new_keys[0]) is None


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
    assert user.days_before_starting == daybefore
    freezer.stop()


@pytest.mark.django_db
def test_personalize(manager_factory, new_hire_factory):
    manager = manager_factory(first_name="jane", last_name="smith")
    new_hire = new_hire_factory(
        first_name="john", last_name="smith", manager=manager, position="developer"
    )

    text = (
        "Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and "
        "you will be our {{ position }}"
    )
    text_without_spaces = (
        "Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you will "
        "be our {{position}}"
    )

    expected_output = (
        "Hello john smith, your manager is jane smith and you will be our developer"
    )

    assert new_hire.personalize(text) == expected_output
    assert new_hire.personalize(text_without_spaces) == expected_output


@pytest.mark.django_db
def test_new_hire_manager(new_hire_factory):
    new_hire_factory(
        slack_user_id="new_slack_id", start_day=datetime.datetime.now().date()
    )
    earlier_nh = new_hire_factory(slack_user_id="new_slack_id2")
    earlier_nh.start_day = datetime.datetime.now().date() - datetime.timedelta(days=2)
    earlier_nh.save()
    should_intro = new_hire_factory(
        is_introduced_to_colleagues=False, start_day=datetime.datetime.now().date()
    )

    assert User.new_hires.without_slack().count() == 1
    assert User.new_hires.with_slack().count() == 2
    assert User.new_hires.starting_today().count() == 2
    assert User.new_hires.to_introduce().count() == 0

    # new hire starts in the future
    should_intro.start_day = datetime.datetime.now().date() + datetime.timedelta(days=2)
    should_intro.save()

    assert User.new_hires.to_introduce().count() == 1


@pytest.mark.django_db
def test_new_hire_has_slack_account(new_hire_factory):
    new_hire_with_slack = new_hire_factory(slack_user_id="test")
    new_hire_without_slack = new_hire_factory()

    assert new_hire_with_slack.has_slack_account
    assert not new_hire_without_slack.has_slack_account
