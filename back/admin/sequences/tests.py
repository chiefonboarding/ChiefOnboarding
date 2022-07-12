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
from admin.introductions.factories import IntroductionFactory
from admin.introductions.forms import IntroductionForm
from admin.preboarding.factories import PreboardingFactory
from admin.preboarding.forms import PreboardingForm
from admin.resources.factories import ResourceFactory
from admin.resources.forms import ResourceForm
from admin.sequences.factories import (
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
    Sequence,
)
from admin.sequences.tasks import timed_triggers
from admin.to_do.factories import ToDoFactory
from admin.to_do.forms import ToDoForm
from admin.to_do.models import ToDo
from organization.models import Notification, Organization


@pytest.mark.django_db
def test_sequence_list_view(client, admin_factory, sequence_factory):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()
    sequence2 = sequence_factory()

    url = reverse("sequences:list")

    response = client.get(url)

    assert sequence1.name in response.content.decode()
    assert sequence2.name in response.content.decode()


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
    assert sequence.conditions.all().first().condition_type == 3
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
            "condition_type": 1,
        },
        follow=True,
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 2
    assert to_do1 in Condition.objects.last().condition_to_do.all()
    assert Condition.objects.last().condition_type == 1

    # Create block based on day/time
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(
        url, {"days": 1, "time": "10:00:00", "condition_type": 0}, follow=True
    )

    assert response.status_code == 200
    assert Condition.objects.all().count() == 3
    assert Condition.objects.last().condition_to_do.all().count() == 0
    assert Condition.objects.last().condition_type == 0

    sequence1.refresh_from_db()
    # All are assinged to this sequence
    assert sequence1.conditions.all().count() == 3


@pytest.mark.django_db
def test_sequence_create_condition_missing_to_do_item_view(
    client, admin_factory, sequence_factory
):
    admin = admin_factory()
    client.force_login(admin)

    sequence1 = sequence_factory()

    # Create block based on to do items
    url = reverse("sequences:condition-create", args=[sequence1.id])
    response = client.post(url, {"condition_type": 1}, follow=True)

    assert response.status_code == 200
    assert "You must add at least one to do item" in response.content.decode()
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

    url = reverse("sequences:timeline", args=[sequence1.id])
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
        ("preboarding", PreboardingForm, PreboardingFactory),
        ("pendingadmintask", PendingAdminTaskForm, PendingAdminTaskFactory),
        ("pendingslackmessage", PendingSlackMessageForm, PendingSlackMessageFactory),
        ("pendingtextmessage", PendingTextMessageForm, PendingTextMessageFactory),
        ("pendingemailmessage", PendingEmailMessageForm, PendingEmailMessageFactory),
    ],
)
def test_sequence_form_view(client, admin_factory, template_type, form, factory):
    admin = admin_factory()
    client.force_login(admin)

    url = reverse("sequences:forms", args=[template_type, 0])
    response = client.get(url)

    response.context["form"] == form()

    item = factory()
    url = reverse("sequences:forms", args=[template_type, item.id])
    response = client.get(url)

    response.context["form"].instance is not None


@pytest.mark.django_db
def test_sequence_unknown_form_view(client, admin_factory):

    admin = admin_factory()
    client.force_login(admin)

    url = reverse("sequences:forms", args=["badddddge", 0])
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200,
            json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
        )
    ),
)
def test_sequence_integration_form_view(
    client, admin_factory, custom_integration_factory
):

    admin = admin_factory()
    client.force_login(admin)
    integration = custom_integration_factory()

    url = reverse("sequences:forms", args=["integration", integration.id])
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
    new_to_do = ToDo.objects.last()
    assert not new_to_do.template
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
    new_to_do = ToDo.objects.last()

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
@pytest.mark.django_db
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200,
            json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
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
    integration = custom_integration_factory()
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
@pytest.mark.django_db
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200,
            json=lambda: {"data": [{"gid": 12, "name": "first team"}]},
        )
    ),
)
def test_sequence_create_custom_integration_form(
    client,
    admin_factory,
    sequence_factory,
    custom_integration_factory,
):
    integration = custom_integration_factory()
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
def test_sequence_open_filled_custom_integration_form(
    client, admin_factory, custom_integration_factory, integration_config_factory
):
    integration = custom_integration_factory()
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

    url = reverse("sequences:forms", args=["integrationconfig", integration_config.id])
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
    response = client.delete(url, follow=True)

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
        ("preboarding", PreboardingFactory),
    ],
)
def test_sequence_default_templates_view(client, admin_factory, template_type, factory):
    admin = admin_factory()
    client.force_login(admin)
    url = reverse("sequences:template_list")

    item = factory()

    response = client.get(url + "?type=" + template_type)

    assert response.status_code == 200
    assert item.name in response.content.decode()


@pytest.mark.django_db
def test_sequence_default_templates_not_valid(client, admin_factory):
    admin = admin_factory()
    client.force_login(admin)
    url = reverse("sequences:template_list")

    response = client.get(url + "?type=pendingadmintask")

    assert response.status_code == 200
    assert len(response.context["object_list"]) == 0


@pytest.mark.django_db
def test_sequence_default_templates_integrations(
    client, admin_factory, integration_factory
):
    admin = admin_factory()
    client.force_login(admin)
    url = reverse("sequences:template_list")
    integration_factory(integration=10)
    integration_factory(integration=10)
    integration_factory(integration=1)
    integration_factory(integration=3)

    response = client.get(url + "?type=integration")

    assert response.status_code == 200
    assert len(response.context["object_list"]) == 2


@pytest.mark.django_db
@freeze_time("2022-05-13")
def test_sequence_trigger_task(
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

    seq.conditions.add(condition)

    # Add sequence to user
    new_hire1.add_sequences([seq])

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
    # It's 4 because the condition creates one as well
    assert Condition.objects.all().count() == 4
    # Not dulicate the template one
    assert ToDo.objects.all().count() == 4
    # Condition one + to_do1
    assert ToDo.templates.all().count() == 2

    # assert Condition.objects.last().to_do.all().count() == 2

    assert "duplicate" in Sequence.objects.last().name


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

    new_hire.add_sequences([sequence])
    assert new_hire.conditions.all().count() == 2

    # Adding it a second time won't change anything
    new_hire.add_sequences([sequence])
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
    new_hire.add_sequences([sequence])

    # there is now one condition (based on todo item)
    assert new_hire.conditions.all().count() == 1

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence])

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
    new_hire.add_sequences([sequence])

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
    new_hire.add_sequences([sequence])

    # there is now one condition (based on todo item)
    assert new_hire.conditions.all().count() == 1

    to_do2 = to_do_factory(template=False)
    to_do3 = to_do_factory()

    condition.to_do.add(to_do2)
    condition.to_do.add(to_do3)

    # Add again to new hire
    new_hire.add_sequences([sequence])

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
    new_hire.add_sequences([sequence])

    # new condition has been added (not merged)
    assert new_hire.conditions.all().count() == 2


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
    new_hire.add_sequences([sequence])

    assert new_hire.to_do.all().count() == 2
    assert new_hire.resources.all().count() == 2
    assert new_hire.introductions.all().count() == 2
    assert new_hire.preboarding.all().count() == 2


@pytest.mark.django_db
def test_pending_email_message_item(pending_email_message_factory):
    pending_email_message = pending_email_message_factory()
    assert pending_email_message.is_email_message
    assert not pending_email_message.is_slack_message
    assert not pending_email_message.is_text_message

    assert pending_email_message.notification_add_type == "sent_email_message"
    assert "mail" in pending_email_message.get_icon_template


@pytest.mark.django_db
def test_pending_text_message_item(pending_text_message_factory):
    pending_text_message = pending_text_message_factory()
    assert not pending_text_message.is_email_message
    assert not pending_text_message.is_slack_message
    assert pending_text_message.is_text_message

    assert pending_text_message.notification_add_type == "sent_text_message"
    assert "message" in pending_text_message.get_icon_template


@pytest.mark.django_db
def test_pending_slack_message_item(pending_slack_message_factory):
    pending_slack_message = pending_slack_message_factory()
    assert not pending_slack_message.is_email_message
    assert pending_slack_message.is_slack_message
    assert not pending_slack_message.is_text_message

    assert pending_slack_message.notification_add_type == "sent_slack_message"
    assert "slack" in pending_slack_message.get_icon_template


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
    pending_text_message = pending_text_message_factory(person_type=0)
    pending_text_message.execute(new_hire)
    # New hire does not have a phone number
    assert Notification.objects.filter(notification_type="failed_no_phone").count() == 1


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
        person_type=0,
    )
    pending_slack_message.execute(new_hire)

    assert cache.get("slack_channel", "slackx")
    assert cache.get(
        "slack_blocks",
        [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Please complete the previous item!, "
                    + new_hire.first_name,
                },
            }
        ],
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    [
        (PendingEmailMessageFactory),
        (PendingAdminTaskFactory),
    ],
)
def test_get_user_function(new_hire_factory, employee_factory, factory):
    item = factory(person_type=0)
    manager = employee_factory()
    buddy = employee_factory()
    new_hire = new_hire_factory(
        manager=manager,
        buddy=buddy,
    )
    assert item.get_user(new_hire) == new_hire

    item = factory(person_type=1)

    assert item.get_user(new_hire) == manager

    item = factory(person_type=2)

    assert item.get_user(new_hire) == buddy

    item = factory(person_type=3)

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
        person_type=1,
    )
    pending_admin_task.execute(new_hire)
    admin_task = AdminTask.objects.first()

    assert AdminTask.objects.all().count() == 1
    assert AdminTaskComment.objects.all().count() == 1
    assert admin_task.assigned_to == manager
    assert admin_task.new_hire == new_hire
