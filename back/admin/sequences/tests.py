import datetime

import pytest
from django.urls import reverse

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
from admin.sequences.models import Condition, Sequence
from admin.to_do.factories import ToDoFactory
from admin.to_do.forms import ToDoForm
from admin.to_do.models import ToDo


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
    assert sequence.update_url() == reverse("sequences:update", args=[sequence.id])
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


# TODO: sequence form integrations


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


# TODO: provision item in sequence


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


# TODO: assign sequence to user


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
    new_hire.conditions.all().count() == 2

    # Adding it a second time won't change anything
    new_hire.add_sequences([sequence])
    new_hire.conditions.all().count() == 2
