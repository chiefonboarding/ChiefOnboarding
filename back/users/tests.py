import datetime

import pytest
from freezegun import freeze_time

from organization.models import Organization
from users.tasks import hourly_check_for_new_hire_send_credentials

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
    assert User.admins.count() == 1
    assert User.managers_and_admins.count() == 2

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
def test_personalize(manager_factory, new_hire_factory, department_factory):
    department = department_factory(name="IT")
    manager = manager_factory(first_name="jane", last_name="smith")
    buddy = manager_factory(email="cat@chiefonboarding.com")
    new_hire = new_hire_factory(
        first_name="john",
        last_name="smith",
        manager=manager,
        buddy=buddy,
        position="developer",
        department=department,
    )

    text = (
        "Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and "
        "you can reach your buddy through {{ buddy_email }}, you will be our "
        "{{ position }} in {{ department }}"
    )
    text_without_spaces = (
        "Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you can "
        "reach your buddy through {{ buddy_email }}, you will be our "
        "{{position}} in {{department}}"
    )

    expected_output = (
        "Hello john smith, your manager is jane smith and you can reach your buddy "
        "through cat@chiefonboarding.com, you will be our developer in IT"
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
        is_introduced_to_colleagues=False,
        start_day=datetime.datetime.now().date() - datetime.timedelta(days=1),
    )

    assert User.new_hires.without_slack().count() == 1
    assert User.new_hires.with_slack().count() == 2
    assert User.new_hires.starting_today().count() == 1
    assert User.new_hires.to_introduce().count() == 1

    # new hire starts in the future
    should_intro.start_day = datetime.datetime.now().date() + datetime.timedelta(days=2)
    should_intro.save()

    assert User.new_hires.to_introduce().count() == 2


@pytest.mark.django_db
def test_new_hire_has_slack_account(new_hire_factory):
    new_hire_with_slack = new_hire_factory(slack_user_id="test")
    new_hire_without_slack = new_hire_factory()

    assert new_hire_with_slack.has_slack_account
    assert not new_hire_without_slack.has_slack_account


@pytest.mark.django_db
def test_daily_check_for_new_hire_send_credentials_task(
    new_hire_factory, mailoutbox, settings
):
    org = Organization.object.get()
    org.timezone = "UTC"  # UTC is the same as on the server
    org.new_hire_email = False
    org.save()

    # 8 am when these notifications get send out
    freezer = freeze_time("2021-01-14 08:00:00", tz_offset=0)  # set UTC
    freezer.start()
    new_hire1 = new_hire_factory(start_day=datetime.datetime.today().date())

    # trigger function manually
    hourly_check_for_new_hire_send_credentials()

    # No emails as new_hire_email is set to false
    assert len(mailoutbox) == 0

    # Enable sending emails
    org.new_hire_email = True
    org.save()

    hourly_check_for_new_hire_send_credentials()
    freezer.stop()

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == f"Welcome to {org.name}!"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == new_hire1.email
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert new_hire1.email in mailoutbox[0].alternatives[0][0]

    freezer = freeze_time("2021-01-14 09:00:00", tz_offset=0)
    freezer.start()
    new_hire1 = new_hire_factory(start_day=datetime.datetime.today().date())

    # trigger function manually
    hourly_check_for_new_hire_send_credentials()

    # No new email as it's 9 am and not 8 am
    assert len(mailoutbox) == 1
    freezer.stop()


@pytest.mark.django_db
def test_new_hire_missing_extra_info(
    condition_to_do_factory,
    integration_config_factory,
    integration_factory,
    new_hire_factory,
):
    integration1 = integration_factory(
        manifest={
            "extra_user_info": [
                {
                    "id": "PERSONAL_EMAIL",
                    "name": "Personal email address",
                    "description": "test",
                }
            ]
        }
    )
    integration2 = integration_factory(
        manifest={
            "extra_user_info": [
                {
                    "id": "PERSONAL_EMAIL",
                    "name": "Personal email address",
                    "description": "test",
                },
                {
                    "id": "NEW_ONE",
                    "name": "Second personal email address",
                    "description": "test2",
                },
            ]
        }
    )
    integration3 = integration_factory(manifest={})
    integration_config1 = integration_config_factory(integration=integration1)
    integration_config2 = integration_config_factory(integration=integration2)
    integration_config3 = integration_config_factory(integration=integration3)
    condition1 = condition_to_do_factory()
    condition2 = condition_to_do_factory()
    condition1.integration_configs.set([integration_config2, integration_config3])
    condition2.integration_configs.set([integration_config1, integration_config2])

    new_hire = new_hire_factory()
    new_hire.conditions.set([condition1, condition2])

    missed_info = new_hire.missing_extra_info

    assert len(missed_info) == 2
    assert missed_info == [
        {
            "id": "PERSONAL_EMAIL",
            "name": "Personal email address",
            "description": "test",
        },
        {
            "id": "NEW_ONE",
            "name": "Second personal email address",
            "description": "test2",
        },
    ]

    new_hire.extra_fields = {"PERSONAL_EMAIL": "hi@chiefonboarding.com"}
    new_hire.save()

    # Remove cache value
    del new_hire.missing_extra_info

    assert len(new_hire.missing_extra_info) == 1

    assert new_hire.missing_extra_info == [
        {
            "id": "NEW_ONE",
            "name": "Second personal email address",
            "description": "test2",
        }
    ]
