import datetime
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from admin.admin_tasks.models import AdminTask, AdminTaskComment
from admin.appointments.factories import AppointmentFactory
from admin.appointments.forms import AppointmentForm
from admin.badges.factories import BadgeFactory
from admin.badges.forms import BadgeForm
from admin.hardware.factories import HardwareFactory
from admin.hardware.forms import HardwareForm
from admin.integrations.models import Integration
from admin.introductions.factories import IntroductionFactory
from admin.introductions.forms import IntroductionForm
from admin.preboarding.factories import PreboardingFactory
from admin.preboarding.forms import PreboardingForm
from admin.resources.factories import ResourceFactory
from admin.resources.forms import ResourceForm
from admin.sequences.emails import send_sequence_message
from admin.sequences.factories import (
    IntegrationConfigFactory,
    PendingAdminTaskFactory,
    PendingEmailMessageFactory,
    PendingSlackMessageFactory,
    PendingTextMessageFactory,
)
from admin.sequences.forms import (
    PendingAdminTaskForm,
    PendingEmailMessageForm,
    PendingSlackMessageForm,
    PendingTextMessageForm,
)
from admin.sequences.models import (
    Condition,
    ExternalMessage,
    IntegrationConfig,
    PendingAdminTask,
    PendingEmailMessage,
    PendingSlackMessage,
    PendingTextMessage,
    Sequence,
)
from admin.sequences.tasks import process_condition, timed_triggers
from admin.to_do.factories import ToDoFactory
from admin.to_do.forms import ToDoForm
from admin.to_do.models import ToDo
from organization.models import Notification, Organization
from slack_bot.models import SlackChannel
from users.models import IntegrationUser


@pytest.mark.django_db
def test_onboarding_sequence_list_view(
    client, admin_factory, sequence_factory, offboarding_sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    sequence2 = sequence_factory()
    sequence3 = offboarding_sequence_factory()

    url = reverse("sequences:list")

    response = client.get(url)

    assert sequence1.name in response.content.decode()
    assert sequence2.name in response.content.decode()
    assert sequence3.name not in response.content.decode()


@pytest.mark.django_db
def test_offboarding_sequence_list_view(
    client, admin_factory, sequence_factory, offboarding_sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    sequence2 = offboarding_sequence_factory()
    sequence3 = offboarding_sequence_factory()

    url = reverse("sequences:offboarding-list")

    response = client.get(url)

    assert sequence1.name not in response.content.decode()
    assert sequence2.name in response.content.decode()
    assert sequence3.name in response.content.decode()


@pytest.mark.django_db
def test_sequence_create_view(client, admin_factory):
    admin = admin_factory()
    client.force_login(admin)

    # No sequences yet
    assert Sequence.objects.all().count() == 0

    # Create one
    url = reverse("sequences:create")
    response = client.get(url, follow=True)

    # Sequence is there now
    assert Sequence.objects.all().count() == 1
    assert Condition.objects.all().count() == 1
    sequence = Sequence.objects.first()
    # Check that condition without actual condition was created
    assert sequence.conditions.all().first().condition_type == Condition.Type.WITHOUT
    assert sequence.update_url == reverse("sequences:update", args=[sequence.id])
    assert sequence.class_name() == "Sequence"
    assert response.redirect_chain[-1][0] == reverse(
        "sequences:update", args=[sequence.id]
    )


@pytest.mark.django_db
def test_sequence_update_name_view(client, admin_factory, sequence_factory):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    url = reverse("sequences:update_name", args=[sequence1.id])
    response = client.post(url, {"name": "test"}, follow=True)

    sequence1.refresh_from_db()
    assert sequence1.name == "test"
    assert response.status_code == 200


@pytest.mark.django_db
def test_sequence_update_department_view(
    client, admin_factory, sequence_factory, department_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    department1 = department_factory()

    assert sequence1.departments.all().count() == 0

    url = reverse("sequences:update_departments", args=[sequence1.id])
    response = client.post(url, {"departments": [department1.id]}, follow=True)

    sequence1.refresh_from_db()
    assert sequence1.departments.all().count() == 1
    assert response.status_code == 200


@pytest.mark.django_db
def test_sequence_create_condition_success_view(
    client, admin_factory, sequence_factory, to_do_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    to_do1 = to_do_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url,
        {
            "condition_to_do": [
                to_do1.id,
            ],
            "condition_type": Condition.Type.TODO,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 2
    assert to_do1 in Condition.objects.last().condition_to_do.all()
    assert Condition.objects.last().condition_type == Condition.Type.TODO

    # Create block based on day/time
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url, {"days": 1, "time": "10:00:00", "condition_type": 0}, follow=True
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 3
    assert Condition.objects.last().condition_to_do.all().count() == 0
    assert Condition.objects.last().condition_type == 0

    # add admin_task to any of the blocks
    condition = Condition.objects.first()
    pending_admin_task = PendingAdminTaskFactory()
    condition.admin_tasks.add(pending_admin_task)

    # Create block based on admin task
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url,
        {
            "condition_type": Condition.Type.ADMIN_TASK,
            "condition_admin_tasks": [pending_admin_task.id],
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 4
    assert Condition.objects.last().condition_admin_tasks.count() == 1
    assert Condition.objects.last().condition_type == Condition.Type.ADMIN_TASK

    sequence1.refresh_from_db()
    # All are assinged to this sequence
    assert sequence1.conditions.all().count() == 4


@pytest.mark.django_db
def test_offboarding_sequence_create_condition_success_view(
    client, admin_factory, offboarding_sequence_factory, to_do_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = offboarding_sequence_factory()
    to_do1 = to_do_factory()
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.get(url)
    assert "On/Before employee&#x27;s last day" in response.content.decode()
    assert "Based on one or more to do items" in response.content.decode()
    assert "Based on one or more admin tasks" in response.content.decode()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url,
        {
            "condition_to_do": [
                to_do1.id,
            ],
            "condition_type": Condition.Type.TODO,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 2
    assert to_do1 in Condition.objects.last().condition_to_do.all()
    assert Condition.objects.last().condition_type == Condition.Type.TODO

    response = client.post(
        url,
        {"condition_type": Condition.Type.BEFORE, "days": -1},
        follow=True,
    )

    assert "Their last day is 0. You cannot go below that." in response.content.decode()
    assert Condition.objects.all().count() == 2


@pytest.mark.django_db
def test_sequence_create_condition_missing_to_do_item_view(
    client, admin_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(url, {"condition_type": Condition.Type.TODO}, follow=True)

    assert response.status_code == 200
    assert "You must add at least one to do item" in response.content.decode()
    # This one is already created by the sequence factory, but no extra has been
    # created due to the call above
    assert Condition.objects.all().count() == 1


@pytest.mark.django_db
def test_sequence_create_condition_missing_admin_task_item_view(
    client, admin_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url, {"condition_type": Condition.Type.ADMIN_TASK}, follow=True
    )

    assert response.status_code == 200
    assert "You must add at least one admin task" in response.content.decode()
    # This one is already created by the sequence factory, but no extra has been
    # created due to the call above
    assert Condition.objects.all().count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload",
    [
        ({"condition_type": 0}),
        ({"days": 1, "condition_type": 0}),
        ({"time": "10:00", "condition_type": 0}),
    ],
)
def test_sequence_create_condition_missing_date_time_view(
    client, admin_factory, sequence_factory, payload
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(url, payload, follow=True)

    assert "Both the time and days have to be filled in." in response.content.decode()
    # This one is already created by the sequence factory, but no extra has been
    # created due to the call above
    assert Condition.objects.all().count() == 1


@pytest.mark.django_db
def test_sequence_create_condition_incorrect_time_view(
    client, admin_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url, {"days": 1, "time": "10:03", "condition_type": 0}, follow=True
    )

    assert (
        "Time must be in an interval of 5 minutes. 3 must end in 0 or 5"
        in response.content.decode()
    )
    # This one is already created by the sequence factory, but no extra has been
    # created due to the call above
    assert Condition.objects.all().count() == 1


@pytest.mark.django_db
def test_sequence_create_condition_incorrect_day_view(
    client, admin_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url, {"days": 0, "time": "10:05", "condition_type": 0}, follow=True
    )

    assert "You cannot use 0 or less." in response.content.decode()
    # This one is already created by the sequence factory, but no extra has been
    # created due to the call above
    assert Condition.objects.all().count() == 1


@pytest.mark.django_db
def test_sequence_update_condition_view(
    client, admin_factory, sequence_factory, condition_timed_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    condition_timed = condition_timed_factory(sequence=sequence1)

    url = reverse("sequences:condition-update", args=[sequence1.id, condition_timed.id])
    response = client.get(url)

    assert str(condition_timed.days) in response.content.decode()
    assert condition_timed.time in response.content.decode()

    response = client.post(
        url, {"days": 11, "time": "10:05", "condition_type": 0}, follow=True
    )

    condition_timed.refresh_from_db()

    assert condition_timed.days == 11
    assert condition_timed.time == datetime.time(10, 5)


@pytest.mark.django_db
def test_sequence_detail_view(
    client, admin_factory, sequence_factory, condition_timed_factory, to_do_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    condition_timed = condition_timed_factory(sequence=sequence1)

    to_do = to_do_factory()
    condition_timed.to_do.add(to_do)

    url = reverse("sequences:update", args=[sequence1.id])
    response = client.get(url)

    assert str(condition_timed.days) in response.content.decode()
    assert "On day" in response.content.decode()
    assert "10 a.m." in response.content.decode()
    assert condition_timed.to_do.all().first().name in response.content.decode()
    assert "new hire" in response.content.decode()
    assert "admins" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "template_type, form, factory",
    [
        ("todo", ToDoForm, ToDoFactory),
        ("resource", ResourceForm, ResourceFactory),
        ("appointment", AppointmentForm, AppointmentFactory),
        ("introduction", IntroductionForm, IntroductionFactory),
        ("badge", BadgeForm, BadgeFactory),
        ("hardware", HardwareForm, HardwareFactory),
        ("preboarding", PreboardingForm, PreboardingFactory),
        ("pendingadmintask", PendingAdminTaskForm, PendingAdminTaskFactory),
        ("pendingslackmessage", PendingSlackMessageForm, PendingSlackMessageFactory),
        ("pendingtextmessage", PendingTextMessageForm, PendingTextMessageFactory),
        ("pendingemailmessage", PendingEmailMessageForm, PendingEmailMessageFactory),
    ],
)
def test_sequence_form_view(
    client, admin_factory, sequence_factory, template_type, form, factory
):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()

    url = reverse("sequences:forms", args=[sequence.id, template_type, 0])
    response = client.get(url)

    response.context["form"] == form(user=admin)

    item = factory()
    url = reverse("sequences:forms", args=[sequence.id, template_type, item.id])
    response = client.get(url)

    response.context["form"].instance is not None


@pytest.mark.django_db
def test_sequence_unknown_form_view(client, admin_factory, sequence_factory):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()

    url = reverse("sequences:forms", args=[sequence.id, "badddddge", 0])
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        return_value=(
            True,
            Mock(
                status_code=200,
                json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
            ),
        )
    ),
)
def test_sequence_integration_form_view(
    client, admin_factory, custom_integration_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()
    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "data_from": "data",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ]
        }
    )

    url = reverse("sequences:forms", args=[sequence.id, "integration", integration.id])
    response = client.get(url)

    assert response.status_code == 200
    assert "TEAM_ID" in response.content.decode()


@pytest.mark.django_db
def test_sequence_unknown_update_form_view(
    client, admin_factory, badge_factory, sequence_factory
):
    badge = badge_factory()
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:update-forms", args=["badddddge", badge.id, condition.id])
    response = client.post(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_sequence_update_form_view(
    client, admin_factory, to_do_factory, sequence_factory
):
    to_do = to_do_factory(template=True)
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:update-forms", args=["todo", 0, condition.id])
    # Create a new to do item
    client.post(
        url, data={"name": "new todo", "due_on_day": 1, "content": '{ "test": "test" }'}
    )

    # Since 'template' was not provided, it will now have two items
    assert ToDo.objects.all().count() == 2
    # The second one is now not a template
    new_to_do = ToDo.objects.get(template=False)
    assert new_to_do.name == "new todo"

    # New item should be added to condition
    condition.refresh_from_db()
    assert condition.to_do.all().count() == 1

    # update the last to do item
    url = reverse("sequences:update-forms", args=["todo", new_to_do.id, condition.id])
    client.post(
        url,
        data={
            "id": new_to_do.id,
            "name": "new todo2",
            "due_on_day": 1,
            "content": '{ "test": "test" }',
        },
    )

    new_to_do.refresh_from_db()
    assert ToDo.objects.all().count() == 2
    assert new_to_do.name == "new todo2"

    # update template item - actually, create a new item from template
    url = reverse("sequences:update-forms", args=["todo", to_do.id, condition.id])
    client.post(
        url,
        data={
            "id": to_do.id,
            "name": to_do.name,
            "due_on_day": 1,
            "content": '{ "test": "test" }',
        },
    )

    assert ToDo.objects.all().count() == 3
    new_to_do = ToDo.objects.order_by("id").last()

    assert to_do.template
    assert not new_to_do.template
    to_do.refresh_from_db()
    assert to_do.name == new_to_do.name

    # New item should be added to condition
    condition.refresh_from_db()
    assert condition.to_do.all().count() == 2


@pytest.mark.django_db
def test_sequence_update_form_with_invalid_info(
    client, admin_factory, to_do_factory, sequence_factory
):
    to_do = to_do_factory(template=True)
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:update-forms", args=["todo", to_do.id, condition.id])
    # Create a new to do item
    response = client.post(url, data={"name": "new todo"})

    assert "This field is required." in response.content.decode()
    assert ToDo.objects.all().count() == 1


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        return_value=(
            True,
            Mock(
                status_code=200,
                json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
            ),
        )
    ),
)
def test_sequence_update_custom_integration_form(
    client,
    admin_factory,
    sequence_factory,
    custom_integration_factory,
    integration_config_factory,
):
    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "data_from": "data",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ],
            "execute": [],
        }
    )
    integration_config = integration_config_factory(integration=integration)
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse(
        "sequences:update-integration-config",
        args=["integrationconfig", integration_config.id, condition.id, 1],
    )
    # Create a new to do item
    client.post(url, data={"TEAM_ID": "12"})

    integration_config.refresh_from_db()
    assert integration_config.additional_data == {"TEAM_ID": "12"}


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        return_value=(
            True,
            Mock(
                status_code=200,
                json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
            ),
        )
    ),
)
def test_sequence_create_custom_integration_form(
    client,
    admin_factory,
    sequence_factory,
    custom_integration_factory,
):
    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "data_from": "data",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ],
            "execute": [],
        }
    )
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse(
        "sequences:update-integration-config",
        args=["integrationconfig", integration.id, condition.id, 0],
    )
    # Create a new to do item
    client.post(url, data={"TEAM_ID": "12"})

    assert IntegrationConfig.objects.all().count() == 1
    integration_config = IntegrationConfig.objects.first()
    assert integration_config.additional_data == {"TEAM_ID": "12"}


@pytest.mark.django_db
def test_sequence_create_manual_custom_integration_form(
    client,
    admin_factory,
    sequence_factory,
    manual_user_provision_integration_factory,
):
    integration = manual_user_provision_integration_factory()
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:forms", args=[sequence.id, "integration", integration.id])

    # get form in modal
    response = client.get(url)
    assert (
        "This is a manual integration, you will have to assign someone to create"
        in response.content.decode()
    )
    assert "Assigned to" in response.content.decode()

    # Create a integration config item
    url = reverse(
        "sequences:update-integration-config",
        args=["integrationconfig", integration.id, condition.id, 0],
    )
    response = client.post(
        url, data={"person_type": IntegrationConfig.PersonType.CUSTOM}
    )
    assert (
        "You must select someone if you want someone custom"
        in response.content.decode()
    )

    response = client.post(
        url,
        data={
            "person_type": IntegrationConfig.PersonType.CUSTOM,
            "assigned_to": admin.id,
        },
    )

    assert IntegrationConfig.objects.all().count() == 1
    integration_config = IntegrationConfig.objects.first()
    assert integration_config.assigned_to == admin


@pytest.mark.django_db
def test_sequence_create_custom_integration_form_input_field(
    client,
    admin_factory,
    sequence_factory,
    custom_integration_factory,
):
    integration = custom_integration_factory(
        manifest={
            "form": [{"id": "USERNAME", "name": "Enter the username", "type": "input"}],
            "execute": [],
        }
    )
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse(
        "sequences:update-integration-config",
        args=["integrationconfig", integration.id, condition.id, 0],
    )
    # Create a new to do item
    client.post(url, data={"USERNAME": "test"})

    assert IntegrationConfig.objects.all().count() == 1
    integration_config = IntegrationConfig.objects.first()
    assert integration_config.additional_data == {"USERNAME": "test"}


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: [{"user": ""}]))),
)
def test_integration_invalid_json_format_returned(
    custom_integration_factory,
    admin_factory,
    sequence_factory,
    client,
):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()
    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "data_from": "data.info",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ]
        }
    )

    url = reverse(
        "sequences:forms",
        args=[sequence.id, "integration", integration.id],
    )
    response = client.get(url)
    assert '"data": {' in response.content.decode()
    assert '"info": [' in response.content.decode()
    assert '"name": "name 0"' in response.content.decode()

    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ]
        }
    )

    url = reverse(
        "sequences:forms",
        args=[sequence.id, "integration", integration.id],
    )
    response = client.get(url)
    assert "{" in response.content.decode()
    assert '"name": "name 0"' in response.content.decode()


@pytest.mark.django_db
def test_sequence_open_filled_custom_integration_form(
    client,
    admin_factory,
    custom_integration_factory,
    integration_config_factory,
    sequence_factory,
):
    integration = custom_integration_factory(
        manifest={
            "form": [
                {
                    "id": "TEAM_ID",
                    "url": "https://example.com/api/1.0/organizations/{{ORG}}/teams",
                    "name": "Select team to add user to",
                    "type": "choice",
                    "data_from": "data",
                    "choice_value": "gid",
                    "choice_name": "name",
                }
            ],
            "execute": [],
        }
    )
    integration_config = integration_config_factory(
        integration=integration, additional_data={"TEAM_ID": "12"}
    )
    manifest = integration_config.integration.manifest
    del manifest["form"][0]["url"]
    manifest["form"][0]["items"] = [{"id": "12", "name": "test team"}]
    del manifest["form"][0]["data_from"]
    del manifest["form"][0]["choice_value"]
    del manifest["form"][0]["choice_name"]
    integration_config.integration.manifest = manifest
    integration_config.integration.save()

    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()

    url = reverse(
        "sequences:forms",
        args=[sequence.id, "integrationconfig", integration_config.id],
    )
    # Create a new to do item
    response = client.get(url)

    assert "selected" in response.content.decode()
    assert "test team" in response.content.decode()


@pytest.mark.django_db
def test_condition_add_item(client, admin_factory, to_do_factory, sequence_factory):
    to_do = to_do_factory(template=True)
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:template_condition", args=[condition.id, "todo", to_do.id])
    # Create a new to do item
    response = client.post(url)

    assert condition.to_do.all().count() == 1
    assert to_do.name in response.content.decode()


@pytest.mark.django_db
def test_condition_remove_item(client, admin_factory, to_do_factory, sequence_factory):
    to_do = to_do_factory(template=True)
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    condition.to_do.add(to_do)
    client.force_login(admin)

    url = reverse("sequences:template_condition", args=[condition.id, "todo", to_do.id])
    client.delete(url)

    assert condition.to_do.all().count() == 0


@pytest.mark.django_db
def test_cannot_delete_condition(client, admin_factory, sequence_factory):
    admin = admin_factory()
    sequence = sequence_factory()
    condition = sequence.conditions.all().first()
    client.force_login(admin)

    url = reverse("sequences:condition-delete", args=[sequence.id, condition.id])
    response = client.delete(url)

    assert response.status_code == 404
    assert sequence.conditions.all().count() == 1


@pytest.mark.django_db
def test_delete_condition(
    client, admin_factory, sequence_factory, condition_to_do_factory
):
    admin = admin_factory()
    sequence = sequence_factory()
    condition2 = condition_to_do_factory(sequence=sequence)

    client.force_login(admin)

    url = reverse("sequences:condition-delete", args=[sequence.id, condition2.id])
    response = client.delete(url)

    assert response.status_code == 200
    assert sequence.conditions.all().count() == 1


@pytest.mark.django_db
def test_delete_sequence(client, admin_factory, sequence_factory):
    admin = admin_factory()
    sequence = sequence_factory()
    client.force_login(admin)
    url = reverse("sequences:delete", args=[sequence.id])
    response = client.post(url, follow=True)

    assert response.status_code == 200

    assert Sequence.objects.all().count() == 0
    assert "Sequence item has been removed" in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "template_type, factory",
    [
        ("todo", ToDoFactory),
        ("resource", ResourceFactory),
        ("appointment", AppointmentFactory),
        ("introduction", IntroductionFactory),
        ("badge", BadgeFactory),
        ("hardware", HardwareFactory),
        ("preboarding", PreboardingFactory),
    ],
)
def test_sequence_default_templates_view(
    client, sequence_factory, admin_factory, template_type, factory
):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()
    url = reverse("sequences:template_list", args=[sequence.id])

    item = factory()

    response = client.get(url + "?type=" + template_type)

    assert response.status_code == 200
    assert item.name in response.content.decode()


@pytest.mark.django_db
def test_sequence_default_templates_not_valid(client, admin_factory, sequence_factory):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()
    url = reverse("sequences:template_list", args=[sequence.id])

    response = client.get(url + "?type=pendingadmintask")

    assert response.status_code == 200
    assert len(response.context["object_list"]) == 0


@pytest.mark.django_db
def test_sequence_item_test_message(client, admin_factory, mailoutbox):
    admin1 = admin_factory()
    admin2 = admin_factory()
    client.force_login(admin1)

    # Actually sending the message to admin2, not admin1
    pending_email_message = PendingEmailMessageFactory(
        send_to=admin2,
        person_type=PendingEmailMessage.PersonType.CUSTOM,
        content_json={
            "time": 0,
            "blocks": [{"data": {"text": "hi {{ first_name }}"}, "type": "paragraph"}],
        },
    )

    url = reverse("sequences:send_test_message", args=[pending_email_message.id])

    client.post(url)

    assert len(mailoutbox) == 1
    # Sending the test mail to admin1
    assert mailoutbox[0].to[0] == admin1.email
    assert admin1.first_name in mailoutbox[0].alternatives[0][0]
    assert admin2.first_name not in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_sequence_default_templates_integrations(
    client,
    admin_factory,
    integration_factory,
    custom_integration_factory,
    sequence_factory,
):
    admin = admin_factory()
    client.force_login(admin)
    sequence = sequence_factory()
    url = reverse("sequences:template_list", args=[sequence.id])
    custom_integration_factory()
    custom_integration_factory()
    integration_factory(integration=Integration.Type.SLACK_BOT)

    response = client.get(url + "?type=integration")

    assert response.status_code == 200
    # only shows the custom ones
    assert len(response.context["object_list"]) == 2


@pytest.mark.django_db
@freeze_time("2022-05-13")
def test_onboarding_sequence_trigger_task(
    sequence_factory,
    new_hire_factory,
    condition_timed_factory,
    to_do_factory,
    resource_factory,
    introduction_factory,
    appointment_factory,
    preboarding_factory,
    badge_factory,
    pending_admin_task_factory,
    pending_text_message_factory,
    manual_user_provision_integration_factory,
):
    org = Organization.object.get()
    # Set it back 5 minutes, so it will actually run through the triggers
    org.timed_triggers_last_check = timezone.now() - timedelta(minutes=5)
    org.save()

    new_hire1 = new_hire_factory()

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    resource1 = resource_factory()
    appointment1 = appointment_factory()
    introduction1 = introduction_factory()
    preboarding1 = preboarding_factory()
    badge1 = badge_factory()
    pending_admin_task1 = pending_admin_task_factory()
    pending_text_message1 = pending_text_message_factory()
    manual_provisioning = manual_user_provision_integration_factory()
    manual_config = IntegrationConfigFactory(integration=manual_provisioning)
    hardware = HardwareFactory()

    seq = sequence_factory()
    unconditioned_condition = seq.conditions.all().first()
    unconditioned_condition.add_item(to_do1)

    # Round current time to 0 or 5 to make it valid entry
    current_time = timezone.now()
    current_time = current_time.replace(
        minute=current_time.minute - (current_time.minute % 5), second=0, microsecond=0
    )

    condition = condition_timed_factory(days=1, time=current_time)
    condition.add_item(to_do2)
    condition.add_item(resource1)
    condition.add_item(appointment1)
    condition.add_item(introduction1)
    condition.add_item(preboarding1)
    condition.add_item(badge1)
    condition.add_item(pending_admin_task1)
    condition.add_item(pending_text_message1)
    condition.add_item(manual_config)
    condition.add_item(hardware)

    seq.conditions.add(condition)

    # Add sequence to user
    new_hire1.add_sequences([seq], new_hire1.get_local_time().date())

    assert new_hire1.to_do.all().count() == 1

    # Trigger sequence conditions
    timed_triggers()

    org.refresh_from_db()
    assert org.timed_triggers_last_check == current_time

    assert new_hire1.to_do.all().count() == 2
    assert new_hire1.resources.all().count() == 1
    assert new_hire1.appointments.all().count() == 1
    assert new_hire1.introductions.all().count() == 1
    assert new_hire1.badges.all().count() == 1
    assert new_hire1.integrations.all().count() == 1
    assert new_hire1.hardware.all().count() == 1


@pytest.mark.django_db
@freeze_time("2022-05-13")
def test_offboarding_sequence_trigger_task(
    offboarding_sequence_factory,
    employee_factory,
    condition_timed_factory,
    to_do_factory,
    resource_factory,
    introduction_factory,
    appointment_factory,
    preboarding_factory,
    badge_factory,
    pending_admin_task_factory,
    pending_text_message_factory,
    manual_user_provision_integration_factory,
):
    org = Organization.object.get()
    # Set it back 5 minutes, so it will actually run through the triggers
    org.timed_triggers_last_check = timezone.now() - timedelta(minutes=5)
    org.save()

    emp1 = employee_factory(termination_date=timezone.now())

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    resource1 = resource_factory()
    appointment1 = appointment_factory()
    introduction1 = introduction_factory()
    preboarding1 = preboarding_factory()
    badge1 = badge_factory()
    pending_admin_task1 = pending_admin_task_factory()
    pending_text_message1 = pending_text_message_factory()
    manual_provisioning = manual_user_provision_integration_factory()
    manual_config = IntegrationConfigFactory(integration=manual_provisioning)

    seq = offboarding_sequence_factory()
    unconditioned_condition = seq.conditions.all().first()
    unconditioned_condition.add_item(to_do1)

    # Round current time to 0 or 5 to make it valid entry
    current_time = timezone.now()
    current_time = current_time.replace(
        minute=current_time.minute - (current_time.minute % 5), second=0, microsecond=0
    )

    condition = condition_timed_factory(
        days=0, time=current_time, condition_type=Condition.Type.BEFORE
    )
    condition.add_item(to_do2)
    condition.add_item(resource1)
    condition.add_item(appointment1)
    condition.add_item(introduction1)
    condition.add_item(preboarding1)
    condition.add_item(badge1)
    condition.add_item(pending_admin_task1)
    condition.add_item(pending_text_message1)
    condition.add_item(manual_config)

    seq.conditions.add(condition)

    # Add sequence to user
    emp1.add_sequences([seq], emp1.get_local_time().date())

    assert emp1.to_do.all().count() == 1

    # Trigger sequence conditions
    timed_triggers()

    org.refresh_from_db()
    assert org.timed_triggers_last_check == current_time

    assert emp1.to_do.all().count() == 2
    assert emp1.resources.all().count() == 1
    assert emp1.appointments.all().count() == 1
    assert emp1.introductions.all().count() == 1
    assert emp1.badges.all().count() == 1
    assert emp1.integrations.all().count() == 1
    assert AdminTask.objects.filter(new_hire=emp1).exists()

    emp1.termination_date = timezone.now() - timedelta(days=2)
    emp1.save()

    # Set it back 5 minutes again, so it will actually run through the triggers
    org.timed_triggers_last_check = timezone.now() - timedelta(minutes=5)
    org.save()

    # Trigger sequence conditions - will be skipped, since it's past termination date
    timed_triggers()

    emp1.refresh_from_db()
    assert emp1.to_do.all().count() == 2
    assert emp1.resources.all().count() == 1
    assert emp1.appointments.all().count() == 1
    assert emp1.introductions.all().count() == 1
    assert emp1.badges.all().count() == 1
    assert emp1.integrations.all().count() == 1
    assert AdminTask.objects.filter(new_hire=emp1).exists()


@pytest.mark.django_db
@freeze_time("2022-05-13")
def test_sequence_trigger_two_people_same_time(
    sequence_factory,
    new_hire_factory,
    condition_timed_factory,
    to_do_factory,
):
    org = Organization.object.get()
    # Set it back 5 minutes, so it will actually run through the triggers
    org.timed_triggers_last_check = timezone.now() - timedelta(minutes=5)
    org.save()

    new_hire1 = new_hire_factory()
    new_hire2 = new_hire_factory()

    to_do1 = to_do_factory()

    seq = sequence_factory()

    # Round current time to 0 or 5 to make it valid entry
    current_time = timezone.now()
    current_time = current_time.replace(
        minute=current_time.minute - (current_time.minute % 5), second=0, microsecond=0
    )

    condition = condition_timed_factory(days=1, time=current_time)
    condition.add_item(to_do1)

    seq.conditions.add(condition)

    # Add sequence to user
    new_hire1.add_sequences([seq], new_hire1.get_local_time().date())
    new_hire2.add_sequences([seq], new_hire2.get_local_time().date())

    assert new_hire1.to_do.all().count() == 0
    assert new_hire2.to_do.all().count() == 0

    # Trigger sequence conditions
    timed_triggers()

    assert new_hire1.to_do.all().count() == 1
    assert new_hire2.to_do.all().count() == 1


# MODEL TESTS


@pytest.mark.django_db
def test_sequence_duplicate(sequence_factory, condition_to_do_factory, to_do_factory):
    sequence = sequence_factory()
    condition = condition_to_do_factory(sequence=sequence)
    to_do1 = to_do_factory()
    to_do2 = to_do_factory(template=False)

    condition.to_do.add(to_do1)
    condition.to_do.add(to_do2)

    sequence.duplicate()

    assert Sequence.objects.all().count() == 2
    # It's 4 because the sequence creates one as well
    assert Condition.objects.all().count() == 4
    # Not dulicate the template one
    assert ToDo.objects.all().count() == 4
    # Condition one + to_do1
    assert ToDo.templates.all().count() == 2

    # assert Condition.objects.last().to_do.all().count() == 2

    assert "duplicate" in Sequence.objects.last().name


@pytest.mark.django_db
def test_sequence_duplicate_with_admin_task_triggers(
    sequence_factory, condition_admin_task_factory, pending_admin_task_factory
):
    sequence = sequence_factory()
    pending_admin_task1 = pending_admin_task_factory()
    pending_admin_task2 = pending_admin_task_factory()

    original_unconditioned_condition = sequence.conditions.first()
    original_unconditioned_condition.admin_tasks.set(
        [pending_admin_task1, pending_admin_task2]
    )

    # create second condition based on the two that are being created
    condition = condition_admin_task_factory(sequence=sequence)
    condition.condition_admin_tasks.set([pending_admin_task1, pending_admin_task2])

    sequence.duplicate()

    assert Sequence.objects.all().count() == 2
    # It's 4 because the sequence creates one as well
    assert Condition.objects.all().count() == 4
    # And now we have 4 admin tasks, as they should all have been duplicated
    assert PendingAdminTask.objects.all().count() == 4

    second_sequence = Sequence.objects.last()
    unconditioned = second_sequence.conditions.first()
    admin_task_pks = unconditioned.admin_tasks.all().values_list("pk", flat=True)

    # admin task conditioned one
    conditioned = second_sequence.conditions.last()
    assert conditioned.based_on_admin_task
    # make sure ids match
    assert conditioned.condition_admin_tasks.filter(id__in=admin_task_pks).count() == 2

    # but don't match with original one (so they are unique)
    assert (
        original_unconditioned_condition.condition_admin_tasks.filter(
            id__in=admin_task_pks
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_sequence_assign_to_user(
    sequence_factory,
    new_hire_factory,
    condition_to_do_factory,
    condition_timed_factory,
    to_do_factory,
):
    new_hire = new_hire_factory()
    sequence = sequence_factory()
    condition = condition_to_do_factory(sequence=sequence)
    condition2 = condition_timed_factory(sequence=sequence)
    to_do1 = to_do_factory()
    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do1)
    condition.to_do.add(to_do2)
    condition2.to_do.add(to_do3)

    new_hire.add_sequences([sequence], new_hire.get_local_time().date())
    assert new_hire.conditions.all().count() == 2

    # Adding it a second time won't change anything
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())
    assert new_hire.conditions.all().count() == 2


@pytest.mark.django_db
def test_sequence_assign_to_user_conditions_on_same_day(
    sequence_factory,
    new_hire_factory,
    condition_timed_factory,
    to_do_factory,
):
    new_hire = new_hire_factory()
    sequence = sequence_factory()
    condition = condition_timed_factory(days=1, time="11:00", sequence=sequence)
    condition2 = condition_timed_factory(days=1, time="10:00", sequence=sequence)
    to_do1 = to_do_factory()
    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do1)
    condition.to_do.add(to_do2)
    condition2.to_do.add(to_do3)

    new_hire.add_sequences([sequence], new_hire.get_local_time().date())
    assert new_hire.conditions.all().count() == 2


@pytest.mark.django_db
def test_sequence_assign_to_user_merge_to_do_condition(
    sequence_factory,
    new_hire_factory,
    condition_to_do_factory,
    to_do_factory,
):
    new_hire = new_hire_factory()
    sequence = sequence_factory()
    condition = condition_to_do_factory(sequence=sequence)
    condition_to_do1 = to_do_factory()
    condition_to_do2 = to_do_factory()
    condition.condition_to_do.add(condition_to_do1)
    condition.condition_to_do.add(condition_to_do2)

    assert condition.condition_to_do.all().count() == 3
    # Condition should merge as the condition conditions match with an existing one

    # Condition has one to do item
    to_do1 = to_do_factory()
    condition.to_do.add(to_do1)

    # Add to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # there is now one condition (based on todo item)
    assert new_hire.conditions.all().count() == 1

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # Condition item was updated and not a new one created
    assert new_hire.conditions.all().count() == 1
    assert new_hire.conditions.all().first().to_do.count() == 3

    # Let's try with a sequence that has a condition slightly different
    sequence = sequence_factory()
    # The auto generated one will be different
    condition = condition_to_do_factory(sequence=sequence)
    condition_to_do1 = to_do_factory()
    condition.condition_to_do.add(condition_to_do1)
    condition.condition_to_do.add(condition_to_do2)

    # add a new to_do item to trigger to the condition
    to_do4 = to_do_factory()
    condition.to_do.add(to_do4)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # new condition has been added (not merged)
    assert new_hire.conditions.all().count() == 2


@pytest.mark.django_db
def test_sequence_assign_to_user_merge_time_condition(
    sequence_factory,
    new_hire_factory,
    condition_timed_factory,
    to_do_factory,
):
    new_hire = new_hire_factory()
    sequence = sequence_factory()
    # Let's try the same with a time based condition
    condition = condition_timed_factory(sequence=sequence)

    # Condition should merge as the condition time/date match with an existing one

    # Condition has one to do item
    to_do1 = to_do_factory()
    condition.to_do.add(to_do1)

    # Add to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # there is now one condition (based on todo item)
    assert new_hire.conditions.all().count() == 1

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # Condition item was updated and not a new one created
    assert new_hire.conditions.all().count() == 1
    assert new_hire.conditions.all().first().to_do.count() == 3

    # Let's try with a sequence that has a condition slightly different
    sequence = sequence_factory()
    # The generated one will be at a different hour
    condition = condition_timed_factory(sequence=sequence, time="09:00")

    # add a new to_do item to trigger to the condition
    to_do4 = to_do_factory()
    condition.to_do.add(to_do4)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # new condition has been added (not merged)
    assert new_hire.conditions.all().count() == 2


@pytest.mark.django_db
def test_sequence_assign_to_user_merge_admin_task_condition(
    sequence_factory,
    new_hire_factory,
    condition_admin_task_factory,
    to_do_factory,
    pending_admin_task_factory,
):
    # Condition should merge as the condition admin_tasks match with an existing one

    new_hire = new_hire_factory()
    sequence = sequence_factory()
    condition = condition_admin_task_factory(sequence=sequence)

    # Condition has two admin task items and will trigger one todo task
    pending_admin_task1 = pending_admin_task_factory()
    pending_admin_task2 = pending_admin_task_factory()
    condition.condition_admin_tasks.set([pending_admin_task1, pending_admin_task2])
    to_do1 = to_do_factory()
    condition.to_do.add(to_do1)

    # Add to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # there is now one condition (based on admin task item)
    assert new_hire.conditions.all().count() == 1
    new_hire_condition = new_hire.conditions.first()
    assert new_hire_condition.based_on_admin_task

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # Condition item was updated and not a new one created
    assert new_hire.conditions.all().count() == 1
    assert new_hire.conditions.all().first().to_do.count() == 3

    # Let's try with a sequence that has a condition slightly different
    sequence = sequence_factory()
    # The generated one will be with only the first admin task from the previous seq
    # in real life, this will never happen as admin tasks will be unique to sequences
    condition = condition_admin_task_factory(sequence=sequence)
    condition.condition_admin_tasks.set([pending_admin_task1])
    to_do3 = to_do_factory()
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # new condition has been added (not merged)
    assert new_hire.conditions.all().count() == 2


@pytest.mark.django_db
def test_sequence_assign_to_user_merge_integrations_revoked_condition(
    sequence_factory,
    new_hire_factory,
    condition_integrations_revoked_factory,
    to_do_factory,
    pending_admin_task_factory,
):
    # Condition should merge as the condition admin_tasks match with an existing one

    new_hire = new_hire_factory()
    sequence = sequence_factory()
    condition = condition_integrations_revoked_factory(sequence=sequence)

    # Condition has two admin task items and will trigger one todo task
    pending_admin_task1 = pending_admin_task_factory()
    pending_admin_task2 = pending_admin_task_factory()
    condition.condition_admin_tasks.set([pending_admin_task1, pending_admin_task2])
    to_do1 = to_do_factory()
    condition.to_do.add(to_do1)

    # Add to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # there is now one condition
    assert new_hire.conditions.all().count() == 1

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    # Condition item was updated and not a new one created
    assert new_hire.conditions.all().count() == 1
    assert new_hire.conditions.all().first().to_do.count() == 3


@pytest.mark.django_db
def test_sequence_add_unconditional_item(
    sequence_factory,
    new_hire_factory,
    to_do_factory,
    resource_factory,
    preboarding_factory,
    introduction_factory,
):
    new_hire = new_hire_factory()
    sequence = sequence_factory()

    unconditional_condition = sequence.conditions.all().first()

    to_do1 = to_do_factory(template=False)
    to_do2 = to_do_factory()

    resource1 = resource_factory(template=False)
    resource2 = resource_factory()

    preboarding1 = preboarding_factory(template=False)
    preboarding2 = preboarding_factory()

    intro1 = introduction_factory()
    intro2 = introduction_factory()

    unconditional_condition.add_item(to_do1)
    unconditional_condition.add_item(to_do2)
    unconditional_condition.add_item(resource1)
    unconditional_condition.add_item(resource2)
    unconditional_condition.add_item(preboarding1)
    unconditional_condition.add_item(preboarding2)
    unconditional_condition.add_item(intro1)
    unconditional_condition.add_item(intro2)

    # Add to new hire
    new_hire.add_sequences([sequence], new_hire.get_local_time().date())

    assert new_hire.to_do.all().count() == 2
    assert new_hire.resources.all().count() == 2
    assert new_hire.introductions.all().count() == 2
    assert new_hire.preboarding.all().count() == 2


@pytest.mark.django_db
def test_pending_email_message_item(
    new_hire_factory, admin_factory, pending_email_message_factory, mailoutbox
):
    new_hire = new_hire_factory(first_name="John")
    admin = admin_factory(first_name="Jane")
    pending_email_message = pending_email_message_factory(
        subject="Hi {{ first_name }}!"
    )
    assert pending_email_message.is_email_message
    assert not pending_email_message.is_slack_message
    assert not pending_email_message.is_text_message

    assert (
        pending_email_message.notification_add_type
        == Notification.Type.SENT_EMAIL_MESSAGE
    )
    assert "mail" in pending_email_message.get_icon_template()

    # Test variable swapping
    send_sequence_message(new_hire, admin, [], pending_email_message.subject)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == f"Hi {new_hire.first_name}!"


@pytest.mark.django_db
def test_notification_execute_pending_email_message_item(
    new_hire_factory, pending_email_message_factory
):
    new_hire = new_hire_factory(first_name="John")
    pending_email_message = pending_email_message_factory(
        subject="Hi {{ first_name }}!"
    )
    pending_email_message.execute(new_hire)

    Notification.objects.count() == 1


@pytest.mark.django_db
def test_pending_text_message_item(pending_text_message_factory):
    pending_text_message = pending_text_message_factory()
    assert not pending_text_message.is_email_message
    assert not pending_text_message.is_slack_message
    assert pending_text_message.is_text_message

    assert (
        pending_text_message.notification_add_type
        == Notification.Type.SENT_TEXT_MESSAGE
    )
    assert "message" in pending_text_message.get_icon_template()


@pytest.mark.django_db
def test_pending_slack_message_item(pending_slack_message_factory):
    pending_slack_message = pending_slack_message_factory()
    assert not pending_slack_message.is_email_message
    assert pending_slack_message.is_slack_message
    assert not pending_slack_message.is_text_message

    assert (
        pending_slack_message.notification_add_type
        == Notification.Type.SENT_SLACK_MESSAGE
    )
    assert "slack" in pending_slack_message.get_icon_template()


@pytest.mark.django_db
def test_duplicate_pending_text_message_item(pending_text_message_factory):
    pending_text_message = pending_text_message_factory()

    old_text_id = pending_text_message.id

    new_pending_text_message = pending_text_message.duplicate()

    ext_message = ExternalMessage.objects.get(id=old_text_id)

    assert ext_message.name == new_pending_text_message.name
    assert ext_message.content == new_pending_text_message.content
    assert ext_message.content_json == new_pending_text_message.content_json
    assert ext_message.send_via == new_pending_text_message.send_via
    assert ext_message.send_to == new_pending_text_message.send_to
    assert ext_message.subject == new_pending_text_message.subject
    assert ext_message.person_type == new_pending_text_message.person_type


@pytest.mark.django_db
def test_execute_external_message_phone_no_number(
    pending_text_message_factory, new_hire_factory
):
    new_hire = new_hire_factory()
    # Send text message to new hire
    pending_text_message = pending_text_message_factory(
        person_type=PendingTextMessage.PersonType.NEWHIRE
    )
    pending_text_message.execute(new_hire)
    # New hire does not have a phone number
    assert (
        Notification.objects.filter(
            notification_type=Notification.Type.FAILED_NO_PHONE
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_execute_external_message_slack(
    pending_slack_message_factory, new_hire_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")
    # Send text message to new hire
    pending_slack_message = pending_slack_message_factory(
        content_json={
            "time": 0,
            "blocks": [
                {
                    "data": {
                        "text": "Please complete the previous item, {{first_name}}!"
                    },
                    "type": "paragraph",
                }
            ],
        },
        person_type=PendingSlackMessage.PersonType.NEWHIRE,
    )
    pending_slack_message.execute(new_hire)

    assert cache.get("slack_channel") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Please complete the previous item, {new_hire.first_name}!",
            },
        }
    ]


@pytest.mark.django_db
def test_execute_external_message_slack_to_slack_channel(
    pending_slack_message_factory, new_hire_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")
    # Send text message to slack channel
    pending_slack_message = pending_slack_message_factory(
        content_json={
            "time": 0,
            "blocks": [
                {
                    "data": {
                        "text": "Please complete the previous item, {{first_name}}!"
                    },
                    "type": "paragraph",
                }
            ],
        },
        person_type=PendingSlackMessage.PersonType.SLACK_CHANNEL,
        send_to_channel=SlackChannel.objects.first(),
    )
    pending_slack_message.execute(new_hire)

    assert cache.get("slack_channel") == "#general"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Please complete the previous item, {new_hire.first_name}!",
            },
        }
    ]


@pytest.mark.django_db
def test_execute_external_message_slack_to_slack_channel_invalid_channel(
    pending_slack_message_factory, new_hire_factory
):
    new_hire = new_hire_factory(slack_user_id="slackx")
    # Send text message to slack channel
    # No slack channel selected
    pending_slack_message = pending_slack_message_factory(
        content_json={
            "time": 0,
            "blocks": [
                {
                    "data": {
                        "text": "Please complete the previous item, {{first_name}}!"
                    },
                    "type": "paragraph",
                }
            ],
        },
        person_type=PendingSlackMessage.PersonType.SLACK_CHANNEL,
    )
    pending_slack_message.execute(new_hire)

    assert cache.get("slack_channel", "") == ""
    assert (
        Notification.objects.filter(
            notification_type=Notification.Type.FAILED_SEND_SLACK_MESSAGE
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_notification_execute_integration_config(
    employee_factory,
    integration_config_factory,
    admin_factory,
    manual_user_provision_integration_factory,
):
    emp1 = employee_factory()

    integration_config = integration_config_factory(
        integration=manual_user_provision_integration_factory()
    )
    integration_config.execute(emp1)

    assert Notification.objects.count() == 1
    assert IntegrationUser.objects.filter(
        user=emp1, integration=integration_config.integration, revoked=False
    ).exists()

    # run once again for offboarding
    emp1 = employee_factory(termination_date=timezone.now())
    integration_config.execute(emp1)
    assert Notification.objects.count() == 2
    assert IntegrationUser.objects.filter(
        user=emp1, integration=integration_config.integration, revoked=True
    ).exists()

    # create admin task based on manager
    admin1 = admin_factory()
    emp2 = employee_factory(manager=admin1)
    integration_config.person_type = IntegrationConfig.PersonType.MANAGER
    integration_config.save()

    integration_config.execute(emp2)
    assert AdminTask.objects.filter(
        new_hire=emp2,
        assigned_to=admin1,
        manual_integration=integration_config.integration,
    ).exists()

    # create admin task based on buddy
    admin2 = admin_factory()
    emp3 = employee_factory(buddy=admin2)
    integration_config.person_type = IntegrationConfig.PersonType.BUDDY
    integration_config.save()

    integration_config.execute(emp3)
    assert AdminTask.objects.filter(
        new_hire=emp3,
        assigned_to=admin2,
        manual_integration=integration_config.integration,
    ).exists()

    # create admin task based on specific person
    admin3 = admin_factory()
    emp4 = employee_factory()
    integration_config.person_type = IntegrationConfig.PersonType.CUSTOM
    integration_config.assigned_to = admin3
    integration_config.save()

    integration_config.execute(emp4)
    assert AdminTask.objects.filter(
        new_hire=emp4,
        assigned_to=admin3,
        manual_integration=integration_config.integration,
    ).exists()


@pytest.mark.django_db
def test_execute_integration_revoke(
    custom_integration_factory,
    condition_to_do_factory,
    employee_factory,
    integration_config_factory,
):
    employee = employee_factory()
    condition = condition_to_do_factory()
    integration = custom_integration_factory(
        manifest={
            "form": [],
            "execute": [{"url": "http://localhost:8000/", "method": "get"}],
            "revoke": [{"url": "http://localhost:8000/", "method": "get"}],
        }
    )
    integration_config = integration_config_factory(integration=integration)
    condition.add_item(integration_config)

    # integration has revoke part, but employee is not being offboarded
    with patch(
        "admin.integrations.models.Integration.execute",
        Mock(return_value=(True, "")),
    ) as execute_mock:
        condition.process_condition(employee, start_date=timezone.now().date())
        assert execute_mock.called

    # integration has revoke part and employee is being offboarded
    employee.termination_date = timezone.now()
    employee.save()

    # revoke part gets triggered
    with patch(
        "admin.integrations.models.Integration.revoke_user",
        Mock(return_value=(True, "")),
    ) as revoke_user_mock:
        condition.process_condition(employee, start_date=timezone.now().date())
        assert revoke_user_mock.called

    integration.manifest = {
        "form": [],
        "execute": [{"url": "http://localhost:8000/", "method": "get"}],
    }
    integration.save()

    # revoke part is gone, we are back at the execute part
    with patch(
        "admin.integrations.models.Integration.execute",
        Mock(return_value=(True, "")),
    ) as execute_mock:
        condition.process_condition(employee, start_date=timezone.now().date())
        assert execute_mock.called


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    [
        (PendingEmailMessageFactory),
        (PendingAdminTaskFactory),
    ],
)
def test_get_user_function(new_hire_factory, employee_factory, factory):
    item = factory(person_type=PendingEmailMessage.PersonType.NEWHIRE)
    manager = employee_factory()
    buddy = employee_factory()
    new_hire = new_hire_factory(
        manager=manager,
        buddy=buddy,
    )
    assert item.get_user(new_hire) == new_hire

    item = factory(person_type=PendingEmailMessage.PersonType.MANAGER)

    assert item.get_user(new_hire) == manager

    item = factory(person_type=PendingEmailMessage.PersonType.BUDDY)

    assert item.get_user(new_hire) == buddy

    item = factory(person_type=PendingEmailMessage.PersonType.CUSTOM)

    if isinstance(item, ExternalMessage):
        assert item.get_user(new_hire) == item.send_to
    else:
        assert item.get_user(new_hire) == item.assigned_to


@pytest.mark.django_db
def test_execute_pending_admin_task(
    pending_admin_task_factory, new_hire_factory, employee_factory
):
    manager = employee_factory()
    new_hire = new_hire_factory(manager=manager)
    pending_admin_task = pending_admin_task_factory(
        comment="test",
        person_type=PendingAdminTask.PersonType.MANAGER,
    )
    pending_admin_task.execute(new_hire)
    admin_task = AdminTask.objects.first()

    assert AdminTask.objects.all().count() == 1
    assert AdminTaskComment.objects.all().count() == 1
    assert admin_task.assigned_to == manager
    assert admin_task.new_hire == new_hire


@pytest.mark.django_db
def test_condition_is_empty(condition_to_do_factory, to_do_factory):
    condition = condition_to_do_factory()
    to_do = to_do_factory()

    assert condition.is_empty
    condition.to_do.add(to_do)
    assert not condition.is_empty


# TASKS


@pytest.mark.django_db
def test_send_slack_message_after_process_condition(
    condition_to_do_factory,
    new_hire_factory,
    to_do_factory,
    resource_factory,
    badge_factory,
):
    from users.models import ResourceUser, ToDoUser

    # Condition with to do item
    condition = condition_to_do_factory()
    to_do = to_do_factory()
    condition.to_do.add(to_do)
    # New hire with Slack account
    new_hire = new_hire_factory(slack_user_id="test")
    new_hire.conditions.add(condition)

    process_condition(condition.id, new_hire.id)

    to_do_user = ToDoUser.objects.last()

    assert cache.get("slack_channel") == "test"

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Here are some new items for you!"},
        },
        {
            "type": "section",
            "block_id": str(to_do_user.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user.id),
                "action_id": f"dialog:to_do:{to_do_user.id}",
            },
        },
    ]

    resource = resource_factory()
    badge = badge_factory()
    condition.resources.add(resource)
    condition.to_do.clear()
    condition.badges.add(badge)

    process_condition(condition.id, new_hire.id)

    resource_user = ResourceUser.objects.last()

    assert cache.get("slack_channel") == "test"

    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Here are some new items for you!"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Congrats, you unlocked: {badge.name} *",
            },
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": "Well done!"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "Well done!"}},
        {
            "type": "section",
            "block_id": str(resource_user.id),
            "text": {"type": "mrkdwn", "text": f"*{resource_user.resource.name}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user.id),
                "action_id": f"dialog:resource:{resource_user.id}",
            },
        },
    ]
