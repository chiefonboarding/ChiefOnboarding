import datetime
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from freezegun import freeze_time

from organization.models import Organization
from users.tasks import hourly_check_for_new_hire_send_credentials

from .models import User


@pytest.mark.django_db
def test_user_create(
    new_hire_factory, admin_factory, employee_factory, manager_factory
):
    new_hire = new_hire_factory()
    admin = admin_factory()
    employee = employee_factory()
    manager = manager_factory()

    assert new_hire.role == get_user_model().Role.NEWHIRE
    assert admin.role == get_user_model().Role.ADMIN
    assert manager.role == get_user_model().Role.MANAGER
    assert employee.role == get_user_model().Role.OTHER

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
    "date, days_before",
    [
        ("2021-01-05", 5),
        ("2021-01-06", 4),
        ("2021-01-07", 3),
        ("2021-01-08", 2),
        ("2021-01-09", 2),  # weekend will be skipped
        ("2021-01-10", 2),  # weekend will be skipped
        ("2021-01-11", 1),
        ("2021-01-12", 0),
        ("2021-01-13", -1),
        ("2021-01-14", -1),
    ],
)
def test_days_before_termination_date(date, days_before, new_hire_factory):
    # Set termination day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(termination_date=datetime.datetime.today().date())
    freezer.stop()

    freezer = freeze_time(date)
    freezer.start()
    assert user.days_before_termination_date == days_before
    freezer.stop()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "date, days_before",
    [
        ("2021-01-05", 5),
        ("2021-01-06", 4),
        ("2021-01-07", 3),
        ("2021-01-08", 2),
        ("2021-01-11", 1),
        ("2021-01-12", 0),
    ],
)
def test_offboarding_workday_to_date(date, days_before, new_hire_factory):
    # Set termination day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = new_hire_factory(termination_date=datetime.datetime.today().date())
    freezer.stop()

    freezer = freeze_time(date)
    freezer.start()
    assert user.offboarding_workday_to_date(days_before).strftime("%Y-%m-%d") == date
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
    assert user1.unique_url != user2.unique_url


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
def test_personalize(
    manager_factory,
    new_hire_factory,
    department_factory,
    custom_integration_factory,
    integration_user_factory,
):
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
    # add integrations
    i_u1 = integration_user_factory(user=new_hire, revoked=True)
    i_u2 = integration_user_factory(user=new_hire, revoked=False)

    integration = custom_integration_factory()

    text = (
        "Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and "
        "you can reach your buddy through {{ buddy_email }}, you will be our "
        "{{ position }} in {{ department }}. He has access to: {{ access_overview }}"
    )
    text_without_spaces = (
        "Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you can "
        "reach your buddy through {{ buddy_email }}, you will be our "
        "{{position}} in {{department}}"
    )

    expected_output = (
        "Hello john smith, your manager is jane smith and you can reach your buddy "
        "through cat@chiefonboarding.com, you will be our developer in IT. He has "
        f"access to: {i_u1.integration.name} (no access), {i_u2.integration.name} (has "
        f"access), {integration.name} (unknown)"
    )

    expected_output_without_spaces = (
        "Hello john smith, your manager is jane smith and you can reach your buddy "
        "through cat@chiefonboarding.com, you will be our developer in IT"
    )

    # Service errored
    with patch(
        "admin.integrations.models.Integration.user_exists",
        Mock(return_value=(None)),
    ):
        assert new_hire.personalize(text) == expected_output
        assert (
            new_hire.personalize(text_without_spaces) == expected_output_without_spaces
        )


@pytest.mark.django_db
def test_check_integration_access(
    new_hire_factory, custom_integration_factory, integration_user_factory
):
    new_hire = new_hire_factory()
    integration_user1 = integration_user_factory(user=new_hire, revoked=True)
    integration_user2 = integration_user_factory(user=new_hire, revoked=False)

    integration = custom_integration_factory()

    # integration service errored
    with patch(
        "admin.integrations.models.Integration.user_exists",
        Mock(return_value=(None)),
    ):
        access = new_hire.check_integration_access()

    assert access[integration_user1.integration.name] is False
    assert access[integration_user2.integration.name] is True
    assert access[integration.name] is None


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
