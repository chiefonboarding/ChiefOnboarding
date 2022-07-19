from datetime import timedelta, datetime
from unittest.mock import Mock, patch

import pytest
from django.contrib import auth
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from admin.appointments.factories import AppointmentFactory
from admin.introductions.factories import IntroductionFactory
from admin.notes.models import Note
from admin.preboarding.factories import PreboardingFactory
from admin.resources.factories import ResourceFactory
from admin.templates.utils import get_user_field
from admin.to_do.factories import ToDoFactory
from misc.models import File
from organization.factories import NotificationFactory
from organization.models import Organization, WelcomeMessage
from users.factories import (
    AdminFactory,
    EmployeeFactory,
    ManagerFactory,
    NewHireFactory,
)
from users.models import CourseAnswer


@pytest.mark.django_db
def test_create_new_hire(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("people:new_hire_add")
    response = client.get(url)

    assert "Add new hire" in response.content.decode()

    # Test required fields, try to create new hire without any data
    response = client.post(url, follow=True)

    assert response.context["form"].errors["first_name"] == ["This field is required."]
    assert response.context["form"].errors["last_name"] == ["This field is required."]
    assert response.context["form"].errors["email"] == ["This field is required."]
    assert response.context["form"].errors["timezone"] == ["This field is required."]
    assert response.context["form"].errors["language"] == ["This field is required."]

    # Create a normal new hire
    response = client.post(
        url,
        {
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "language": "en",
            "timezone": "UTC",
            "start_day": "2022-05-06",
        },
        follow=True,
    )

    assert "New hire has been created" in response.content.decode()

    assert get_user_model().objects.all().count() == 2
    assert get_user_model().objects.first().role == 1
    assert get_user_model().objects.last().role == 0

    url = reverse("people:new_hire", args=[get_user_model().objects.last().id])
    response = client.get(url)

    assert "A new hire has been added" in response.content.decode()


@pytest.mark.django_db
def test_create_new_hire_with_sequences(
    client,
    django_user_model,
    sequence_factory,
    condition_timed_factory,
    condition_to_do_factory,
    to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    sequence = sequence_factory()
    condition1 = condition_timed_factory(sequence=sequence, days=1)
    condition2 = condition_to_do_factory(sequence=sequence)
    condition1.to_do.add(to_do1)
    condition2.to_do.add(to_do2)

    url = reverse("people:new_hire_add")
    response = client.post(
        url,
        {
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "language": "en",
            "timezone": "UTC",
            "start_day": timezone.now().date() - timedelta(days=2),
            "sequences": [sequence.id],
        },
        follow=True,
    )

    # To do item in condition is passed time, so we should notify user of that

    assert "Items that will never be triggered" in response.content.decode()
    assert to_do1.name in response.content.decode()
    # Second to do will not show up as triggers based on to do items are not shown there
    assert to_do2.name not in response.content.decode()


@pytest.mark.django_db
def test_create_new_hire_with_sequences_before_starting(
    client,
    django_user_model,
    sequence_factory,
    condition_timed_factory,
    condition_to_do_factory,
    to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    to_do3 = to_do_factory()
    sequence = sequence_factory()
    # before starting
    condition1 = condition_timed_factory(sequence=sequence, days=1, condition_type=2)
    condition2 = condition_to_do_factory(sequence=sequence)
    # after starting
    condition3 = condition_timed_factory(sequence=sequence, days=1)
    condition1.to_do.add(to_do1)
    condition2.to_do.add(to_do2)
    condition3.to_do.add(to_do3)

    url = reverse("people:new_hire_add")
    response = client.post(
        url,
        {
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "language": "en",
            "timezone": "UTC",
            "start_day": timezone.now().date() + timedelta(days=7),
            "sequences": [sequence.id],
        },
        follow=True,
    )

    # To do item in condition is passed time, so we should notify user of that
    assert "Items that will never be triggered" in response.content.decode()
    assert to_do1.name in response.content.decode()
    assert to_do3.name not in response.content.decode()
    # Second to do will not show up as triggers based on to do items are not shown there
    assert to_do2.name not in response.content.decode()


@pytest.mark.django_db
def test_create_new_hire_add_sequence_with_manual_trigger_condition(
    client,
    django_user_model,
    new_hire_factory,
    sequence_factory,
    condition_timed_factory,
    condition_to_do_factory,
    to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    new_hire1 = new_hire_factory()
    sequence = sequence_factory()
    condition1 = condition_timed_factory(sequence=sequence, days=1)
    condition2 = condition_to_do_factory(sequence=sequence)
    condition1.to_do.add(to_do1)
    condition2.to_do.add(to_do2)

    url = reverse("people:add_sequence", args=[new_hire1.id])
    response = client.get(url)

    assert sequence.name in response.content.decode()

    response = client.post(url, data={"sequences": [sequence.id]}, follow=True)

    assert "Items that will never be triggered" in response.content.decode()
    assert to_do1.name in response.content.decode()
    assert "Trigger all these items now" in response.content.decode()

    assert new_hire1.to_do.count() == 0
    assert new_hire1.total_tasks == 0
    assert new_hire1.completed_tasks == 0

    url = reverse("people:trigger-condition", args=[new_hire1.id, condition1.id])
    response = client.post(url, follow=True)

    new_hire1.refresh_from_db()
    # to do item got added from condition
    assert new_hire1.to_do.count() == 1
    # two to do items in total scheduled/added to new hire
    assert new_hire1.total_tasks == 2
    assert new_hire1.completed_tasks == 0

    assert "Done!" in response.content.decode()


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_create_new_hire_add_sequence_with_manual_trigger_condition_before_starting(
    client,
    django_user_model,
    new_hire_factory,
    sequence_factory,
    condition_timed_factory,
    condition_to_do_factory,
    to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do1 = to_do_factory()
    to_do2 = to_do_factory()
    to_do3 = to_do_factory()
    new_hire1 = new_hire_factory(start_day=timezone.now() - timedelta(days=1))
    sequence = sequence_factory()
    condition1 = condition_timed_factory(sequence=sequence, days=2)
    condition2 = condition_to_do_factory(sequence=sequence)
    condition3 = condition_to_do_factory(sequence=sequence, days=1, condition_type=2)
    condition1.to_do.add(to_do1)
    condition2.to_do.add(to_do2)
    condition3.to_do.add(to_do3)

    url = reverse("people:add_sequence", args=[new_hire1.id])
    response = client.get(url)

    assert sequence.name in response.content.decode()

    response = client.post(url, data={"sequences": [sequence.id]}, follow=True)

    assert "Items that will never be triggered" in response.content.decode()
    assert to_do1.name in response.content.decode()
    assert to_do3.name in response.content.decode()
    assert "Trigger all these items now" in response.content.decode()

    assert new_hire1.to_do.count() == 0

    url = reverse("people:trigger-condition", args=[new_hire1.id, condition1.id])
    response = client.post(url, follow=True)

    new_hire1.refresh_from_db()
    # to do item got added from condition
    assert new_hire1.to_do.count() == 1
    assert "Done!" in response.content.decode()


@pytest.mark.django_db
def test_create_new_hire_add_sequence_without_manual_trigger_condition_redirect_back(
    client,
    django_user_model,
    new_hire_factory,
    sequence_factory,
    condition_timed_factory,
    condition_to_do_factory,
    to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do1 = to_do_factory()
    new_hire1 = new_hire_factory()
    sequence = sequence_factory()
    condition1 = condition_timed_factory(sequence=sequence, days=3)
    condition1.to_do.add(to_do1)

    url = reverse("people:add_sequence", args=[new_hire1.id])
    response = client.post(url, data={"sequences": [sequence.id]}, follow=True)

    assert (
        reverse("admin:new_hire", args=[new_hire1.id]) == response.redirect_chain[-1][0]
    )


@pytest.mark.django_db
def test_new_hire_list_view(client, new_hire_factory, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    # create 20 new hires
    new_hire_factory.create_batch(20)

    url = reverse("people:new_hires")
    response = client.get(url)

    assert "New hires" in response.content.decode()

    assert len(response.context["object_list"]) == 10

    # Check if pagination works
    assert "last" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_to_do_sequence_item(
    client,
    new_hire_factory,
    django_user_model,
    to_do_user_factory,
    condition_to_do_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    condition = condition_to_do_factory()
    new_hire1 = new_hire_factory()
    new_hire1.conditions.add(condition)
    # Uncompleted to do item
    to_do_user = to_do_user_factory(user=new_hire1)
    condition.condition_to_do.set([to_do_user.to_do])

    url = reverse("people:new_hire", args=[new_hire1.id])
    response = client.get(url)

    assert '"badge bg-blue-lt mt-1"' in response.content.decode()
    assert "bg-green-lt" not in response.content.decode()

    to_do_user.completed = True
    to_do_user.save()

    response = client.get(url)
    assert "bg-blue-lt" not in response.content.decode()
    assert "bg-green-lt" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_latest_activity(client, new_hire_factory, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()
    new_hire2 = new_hire_factory()

    url = reverse("people:new_hire", args=[new_hire1.id])
    response = client.get(url)

    # There shouldn't be any items yet
    assert "Latest activity" in response.content.decode()
    assert "No items yet" in response.content.decode()

    # Let's create a few
    not1 = NotificationFactory(
        notification_type="added_todo", created_for=new_hire1, public_to_new_hire=True
    )
    not2 = NotificationFactory(
        notification_type="completed_course",
        created_for=new_hire1,
        public_to_new_hire=False,
    )
    not3 = NotificationFactory(
        notification_type="added_introduction",
        created_for=new_hire2,
        public_to_new_hire=True,
    )

    # Reload page
    url = reverse("people:new_hire", args=[new_hire1.id])
    response = client.get(url)

    # First note should appear
    assert not1.extra_text in response.content.decode()
    assert not1.get_notification_type_display() in response.content.decode()

    assert not2.extra_text in response.content.decode()
    assert not2.get_notification_type_display() in response.content.decode()

    # For different user
    assert not3.extra_text not in response.content.decode()
    assert not3.get_notification_type_display() not in response.content.decode()


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_send_preboarding_send_menu_option(client, new_hire_factory, django_user_model):
    # Test if send preboarding menu option is available
    # Should only be available before start date
    client.force_login(django_user_model.objects.create(role=1))
    new_hire = new_hire_factory(start_day=datetime.fromisoformat("2022-05-15"))

    url = reverse("people:new_hire", args=[new_hire.id])
    response = client.get(url)

    assert "Send Preboarding email" in response.content.decode()

    new_hire.start_day -= timedelta(days=2)
    new_hire.save()

    url = reverse("people:new_hire", args=[new_hire.id])
    response = client.get(url)

    assert "Send Preboarding email" not in response.content.decode()


@pytest.mark.django_db
def test_send_preboarding_message_via_email(
    client, settings, new_hire_factory, django_user_model, mailoutbox
):
    settings.BASE_URL = "https://chiefonboarding.com"
    settings.TWILIO_ACCOUNT_SID = ""

    client.force_login(django_user_model.objects.create(role=1))

    org = Organization.object.get()
    new_hire1 = new_hire_factory()
    url = reverse("people:send_preboarding_notification", args=[new_hire1.id])

    # Add personalize option to test
    wm = WelcomeMessage.objects.get(language="en", message_type=0)
    wm.message += " {{ first_name }} "
    wm.save()

    # Add preboarding item to test link
    preboarding = PreboardingFactory()  # noqa
    new_hire1.preboarding.add(preboarding)

    response = client.get(url)

    assert "Send preboarding notification" in response.content.decode()

    # Twillio is not set up, so only email option
    assert "Send via text" not in response.content.decode()
    assert "Send via email" in response.content.decode()

    response = client.post(url, data={"send_type": "email"}, follow=True)

    assert response.status_code == 200
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == f"Welcome to {org.name}!"
    assert new_hire1.first_name in mailoutbox[0].alternatives[0][0]
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == new_hire1.email
    assert (
        settings.BASE_URL
        + reverse("new_hire:preboarding-url")
        + "?token="
        + new_hire1.unique_url
        in mailoutbox[0].alternatives[0][0]
    )

    # Check if url in email is valid
    response = client.get(
        reverse("new_hire:preboarding-url") + "?token=" + new_hire1.unique_url,
        follow=True,
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_send_preboarding_message_via_text(
    client, settings, new_hire_factory, django_user_model
):
    settings.BASE_URL = "https://chiefonboarding.com"
    settings.TWILIO_ACCOUNT_SID = "test"

    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()
    url = reverse("people:send_preboarding_notification", args=[new_hire1.id])

    # Add personalize option to test
    wm = WelcomeMessage.objects.get(language="en", message_type=0)
    wm.message += " {{ first_name }} "
    wm.save()

    # Add preboarding item to test link
    preboarding = PreboardingFactory()
    new_hire1.preboarding.add(preboarding)

    response = client.get(url)

    # Twillio is set up, so both email and text option
    assert "Send via text" in response.content.decode()
    assert "Send via email" in response.content.decode()


@pytest.mark.django_db
def test_send_login_email(  # after first day email
    client, settings, new_hire_factory, django_user_model, mailoutbox
):
    settings.BASE_URL = "https://chiefonboarding.com"

    client.force_login(django_user_model.objects.create(role=1))

    org = Organization.object.get()
    new_hire1 = new_hire_factory()
    url = reverse("people:send_login_email", args=[new_hire1.id])

    # Add personalize option to test
    wm = WelcomeMessage.objects.get(language="en", message_type=1)
    wm.message += " {{ first_name }} "
    wm.save()

    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert "Sent email to new hire" in response.content.decode()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == f"Welcome to {org.name}!"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == new_hire1.email
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert new_hire1.first_name in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_new_hire_profile(client, new_hire_factory, admin_factory, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()
    admin1 = admin_factory(email="jo@chiefonboarding.com")
    admin2 = admin_factory()
    url = reverse("people:new_hire_profile", args=[new_hire1.id])

    response = client.get(url)

    assert response.status_code == 200
    # Check that first name field is populated
    assert (
        'name="first_name" value="' + new_hire1.first_name + '"'
        in response.content.decode()
    )

    # Let's update the new hire
    new_data = {
        "first_name": "Stan",
        "last_name": "Doe",
        "email": "stan@chiefonboarding.com",
        "timezone": "UTC",
        "start_day": "2021-01-20",
        "language": "nl",
        "buddy": admin1.id,
        "manager": admin2.id,
    }
    response = client.post(url, data=new_data, follow=True)

    # Get record from database
    new_hire1.refresh_from_db()

    assert response.status_code == 200
    assert f'<option value="{admin1.id}" selected>' in response.content.decode()
    assert f'<option value="{admin2.id}" selected>' in response.content.decode()
    assert new_hire1.first_name == "Stan"
    assert new_hire1.last_name == "Doe"
    assert new_hire1.email == "stan@chiefonboarding.com"
    assert "New hire has been updated" in response.content.decode()

    # Let's update again, but now with already used email
    new_data["email"] = "jo@chiefonboarding.com"
    response = client.post(url, data=new_data, follow=True)

    new_hire1.refresh_from_db()

    assert response.status_code == 200
    assert new_hire1.email != "jo@chiefonboarding.com"
    assert "User with this Email already exists." in response.content.decode()
    assert "New hire has been updated" not in response.content.decode()


@pytest.mark.django_db
def test_migrate_new_hire_to_normal_account(
    client, new_hire_factory, django_user_model
):
    admin = django_user_model.objects.create(role=1)
    client.force_login(admin)

    # Doesn't work for admins
    url = reverse("people:migrate-to-normal", args=[admin.id])
    response = client.post(url, follow=True)
    admin.refresh_from_db()

    assert response.status_code == 404
    assert admin.role == 1

    # Check with new hire
    new_hire1 = new_hire_factory()
    url = reverse("people:migrate-to-normal", args=[new_hire1.id])

    response = client.post(url, follow=True)

    new_hire1.refresh_from_db()

    assert response.status_code == 200
    assert "New hire is now a normal account." in response.content.decode()
    assert new_hire1.role == 3

    # Check if removed from new hires page
    url = reverse("people:new_hires")
    response = client.get(url)

    assert new_hire1.full_name not in response.content.decode()


@pytest.mark.django_db
def test_new_hire_delete(client, django_user_model, new_hire_factory):
    admin = django_user_model.objects.create(role=1)
    client.force_login(admin)

    # Doesn't work for admins
    url = reverse("people:delete", args=[admin.id])
    response = client.post(url, follow=True)
    admin.refresh_from_db()
    assert django_user_model.objects.all().count() == 1

    new_hire1 = new_hire_factory()
    # We have two users now
    assert django_user_model.objects.all().count() == 2

    # Works for new hires
    url = reverse("people:delete", args=[new_hire1.id])
    response = client.post(url, follow=True)

    assert django_user_model.objects.all().count() == 1
    assert "New hire has been removed" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_notes(client, note_factory, django_user_model):
    admin = django_user_model.objects.create(role=1)
    client.force_login(admin)

    # create two random notes
    note1 = note_factory()
    note2 = note_factory()

    url = reverse("people:new_hire_notes", args=[note1.new_hire.id])
    response = client.get(url)

    assert response.status_code == 200
    # First note should show
    assert note1.content in response.content.decode()
    assert note1.admin.full_name in response.content.decode()
    # Second note should not show
    assert note2.content not in response.content.decode()
    assert note2.admin.full_name not in response.content.decode()

    data = {"content": "new note!"}
    response = client.post(url, data=data, follow=True)

    assert response.status_code == 200
    assert Note.objects.all().count() == 3
    assert "Note has been added" in response.content.decode()
    assert "new note!" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_list_welcome_messages(
    client, new_hire_welcome_message_factory, django_user_model
):
    admin = django_user_model.objects.create(role=1)
    client.force_login(admin)

    # create two random welcome messages
    wm1 = new_hire_welcome_message_factory()
    wm2 = new_hire_welcome_message_factory()

    url = reverse("people:new_hire_welcome_messages", args=[wm1.new_hire.id])
    response = client.get(url)

    assert response.status_code == 200
    # First welcome message should show
    assert wm1.message in response.content.decode()
    assert wm1.colleague.full_name in response.content.decode()
    # Second welcome message should not show (not from this user)
    assert wm2.message not in response.content.decode()
    assert wm2.colleague.full_name not in response.content.decode()


@pytest.mark.django_db
def test_new_hire_admin_tasks(
    client, new_hire_factory, django_user_model, admin_task_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    url = reverse("people:new_hire_admin_tasks", args=[new_hire1.id])
    response = client.get(url)

    assert response.status_code == 200
    assert "There are no open items" in response.content.decode()
    assert "There are no closed items" in response.content.decode()
    assert "Open admin tasks" in response.content.decode()
    assert "Completed admin tasks" in response.content.decode()

    admin_task1 = admin_task_factory(new_hire=new_hire1)

    response = client.get(url)
    assert "There are no open items" not in response.content.decode()
    assert admin_task1.name in response.content.decode()
    assert "There are no closed items" in response.content.decode()

    admin_task2 = admin_task_factory(new_hire=new_hire1, completed=True)

    response = client.get(url)
    assert "There are no open items" not in response.content.decode()
    assert admin_task1.name in response.content.decode()
    assert admin_task2.name in response.content.decode()
    assert "There are no closed items" not in response.content.decode()


@pytest.mark.django_db
def test_new_hire_forms(
    client, new_hire_factory, django_user_model, to_do_user_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    url = reverse("people:new_hire_forms", args=[new_hire1.id])
    response = client.get(url)

    assert "This new hire has not filled in any forms yet" in response.content.decode()

    to_do_user_factory(
        user=new_hire1,
        form=[
            {
                "id": "DkDqXc6e5q",
                "data": {"text": "single line", "type": "input"},
                "type": "form",
                "answer": "test1",
            },
            {
                "id": "4mjTrlsdAW",
                "data": {"text": "Multi line", "type": "text"},
                "type": "form",
                "answer": "test12",
            },
            {
                "id": "-l-2D9wbK0",
                "data": {"text": "Checkbox", "type": "check"},
                "type": "form",
                "answer": "on",
            },
            {
                "id": "mlaegf2eHM",
                "data": {"text": "Upload", "type": "upload"},
                "type": "form",
                "answer": "1",
            },
        ],
        completed=True,
    )

    # Create fake file, otherwise templatetag will crash
    File.objects.create(name="testfile", ext="png", key="testfile.png")

    response = client.get(url)

    assert "To do forms" in response.content.decode()
    assert "test1" in response.content.decode()
    assert "test12" in response.content.decode()
    assert "checkbox" in response.content.decode()
    assert "Download user uploaded file" in response.content.decode()

    assert "Preboarding forms" not in response.content.decode()
    assert (
        "This new hire has not filled in any forms yet" not in response.content.decode()
    )


@pytest.mark.django_db
def test_new_hire_progress(
    client, new_hire_factory, django_user_model, to_do_user_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    url = reverse("people:new_hire_progress", args=[new_hire1.id])

    response = client.get(url)

    assert (
        "There are no todo items or resources assigned to this user"
        in response.content.decode()
    )

    to_do_user1 = to_do_user_factory(user=new_hire1)

    response = client.get(url)

    assert to_do_user1.to_do.name in response.content.decode()
    assert "checked" not in response.content.decode()
    assert "Remind" in response.content.decode()

    to_do_user1.completed = True
    to_do_user1.save()

    # Get page again
    response = client.get(url)

    assert to_do_user1.to_do.name in response.content.decode()
    assert "checked" in response.content.decode()
    assert "Reopen" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_course_rating(
    resource_user_factory, resource_with_level_deep_chapters_factory, chapter_factory
):
    resource = resource_with_level_deep_chapters_factory(course=True)

    # In total 3 questions
    question_chapter = resource.chapters.get(type=2)
    question_chapter.content = {
        "time": 0,
        "blocks": [
            {
                "id": "1",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "1", "text": "first option"},
                    {"id": "2", "text": "second option"},
                ],
                "answer": "2",
            }
        ],
    }
    question_chapter.save()

    new_chapter = chapter_factory(
        name="top_lvl4_q", resource=resource, type=2, order=11
    )
    new_chapter.content = {
        "time": 0,
        "blocks": [
            {
                "id": "2",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "3", "text": "first option"},
                    {"id": "4", "text": "second option"},
                ],
                "answer": "4",
            },
            {
                "id": "3",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "5", "text": "first option"},
                    {"id": "6", "text": "second option"},
                ],
                "answer": "5",
            },
        ],
    }
    new_chapter.save()
    resource_user1 = resource_user_factory(resource=resource)

    # No questions have been answered yet, so n/a
    assert resource_user1.get_rating == "n/a"

    # Correct answer
    answer_obj = CourseAnswer.objects.create(
        chapter=question_chapter, answers={"item-0": "2"}
    )
    resource_user1.answers.add(answer_obj)

    assert resource_user1.get_rating == "1 correct answers out of 1 questions"

    # First one is wrong, second one is right
    answer_obj = CourseAnswer.objects.create(
        chapter=new_chapter, answers={"item-0": "3", "item-1": "5"}
    )
    resource_user1.answers.add(answer_obj)

    assert resource_user1.get_rating == "2 correct answers out of 3 questions"


@pytest.mark.django_db
def test_new_hire_course_answers_list(
    client,
    django_user_model,
    resource_user_factory,
    resource_with_level_deep_chapters_factory,
    chapter_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    resource = resource_with_level_deep_chapters_factory(course=True)

    # In total 3 questions
    question_chapter = resource.chapters.get(type=2)
    question_chapter.content = {
        "time": 0,
        "blocks": [
            {
                "id": "1",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "1", "text": "first option"},
                    {"id": "2", "text": "second option"},
                ],
                "answer": "2",
            }
        ],
    }
    question_chapter.save()

    new_chapter = chapter_factory(
        name="top_lvl4_q", resource=resource, type=2, order=11
    )
    new_chapter.content = {
        "time": 0,
        "blocks": [
            {
                "id": "2",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "3", "text": "third option"},
                    {"id": "4", "text": "fourth option"},
                ],
                "answer": "4",
            },
            {
                "id": "3",
                "type": "question",
                "content": "Please answer this question",
                "items": [
                    {"id": "5", "text": "fifth option"},
                    {"id": "6", "text": "sixth option"},
                ],
                "answer": "5",
            },
        ],
    }
    new_chapter.save()
    resource_user1 = resource_user_factory(resource=resource)

    # No questions have been answered yet, so n/a
    assert resource_user1.get_rating == "n/a"

    url = reverse(
        "admin:new-hire-course-answers",
        args=[resource_user1.user.id, resource_user1.id],
    )

    response = client.get(url)

    assert "No answers were given in yet." in response.content.decode()

    # Correct answer
    answer_obj = CourseAnswer.objects.create(
        chapter=question_chapter, answers={"item-0": "2"}
    )
    resource_user1.answers.add(answer_obj)

    response = client.get(url)

    assert "Answer given by new hire: second option" in response.content.decode()

    # First one is wrong, second one is right
    answer_obj = CourseAnswer.objects.create(
        chapter=new_chapter, answers={"item-0": "3", "item-1": "5"}
    )
    resource_user1.answers.add(answer_obj)

    response = client.get(url)

    assert "Answer given by new hire: third option" in response.content.decode()
    assert "Answer given by new hire: fifth option" in response.content.decode()


@pytest.mark.django_db
def test_new_hire_reopen_todo(
    client, settings, django_user_model, to_do_user_factory, mailoutbox
):
    client.force_login(django_user_model.objects.create(role=1))
    to_do_user1 = to_do_user_factory()

    # not a valid template type
    url = reverse("people:new_hire_reopen", args=["todouser1", to_do_user1.id])
    response = client.get(url, follow=True)
    assert response.status_code == 404

    url = reverse("people:new_hire_reopen", args=["todouser", to_do_user1.id])

    response = client.post(url, data={"message": "You forgot this one!"}, follow=True)

    assert response.status_code == 200
    assert "Item has been reopened" in response.content.decode()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please redo this task"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == to_do_user1.user.email
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert "You forgot this one!" in mailoutbox[0].alternatives[0][0]
    assert to_do_user1.user.first_name in mailoutbox[0].alternatives[0][0]

    new_hire = to_do_user1.user
    new_hire.slack_user_id = "slackx"
    new_hire.save()

    response = client.post(url, data={"message": "You forgot this one!"}, follow=True)

    assert cache.get("slack_channel") == to_do_user1.user.slack_user_id
    assert cache.get("slack_blocks") == [
        {"type": "section", "text": {"type": "mrkdwn", "text": "You forgot this one!"}},
        {
            "type": "section",
            "block_id": str(to_do_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_do_user1.to_do.name}*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user1.id),
                "action_id": f"dialog:to_do:{to_do_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_new_hire_reopen_course(
    client, settings, django_user_model, resource_user_factory, mailoutbox
):
    client.force_login(django_user_model.objects.create(role=1))

    resource_user1 = resource_user_factory(resource__course=True)

    url = reverse("people:new_hire_reopen", args=["resourceuser", resource_user1.id])

    response = client.post(url, data={"message": "You forgot this one!"}, follow=True)

    assert response.status_code == 200
    assert "Item has been reopened" in response.content.decode()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please redo this task"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == resource_user1.user.email
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert "You forgot this one!" in mailoutbox[0].alternatives[0][0]
    assert resource_user1.user.first_name in mailoutbox[0].alternatives[0][0]

    new_hire = resource_user1.user
    new_hire.slack_user_id = "slackx"
    new_hire.save()

    response = client.post(url, data={"message": "You forgot this one!"}, follow=True)

    assert cache.get("slack_channel") == resource_user1.user.slack_user_id
    assert cache.get("slack_blocks") == [
        {"type": "section", "text": {"type": "mrkdwn", "text": "You forgot this one!"}},
        {
            "type": "section",
            "block_id": str(resource_user1.id),
            "text": {"type": "mrkdwn", "text": f"*{resource_user1.resource.name}*"},
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View course"},
                "style": "primary",
                "value": str(resource_user1.id),
                "action_id": f"dialog:resource:{resource_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_new_hire_remind_to_do(
    client, settings, django_user_model, to_do_user_factory, mailoutbox
):
    client.force_login(django_user_model.objects.create(role=1))

    to_do_user1 = to_do_user_factory()

    # not a valid template type
    url = reverse("people:new_hire_remind", args=["todouser1", to_do_user1.id])
    response = client.post(url, follow=True)
    assert response.status_code == 404

    url = reverse("people:new_hire_remind", args=["todouser", to_do_user1.id])

    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert "Reminder has been sent!" in response.content.decode()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please complete this task"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == to_do_user1.user.email
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert to_do_user1.to_do.name in mailoutbox[0].alternatives[0][0]
    assert to_do_user1.user.first_name in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_new_hire_remind_to_do_slack_message(
    client, settings, django_user_model, to_do_user_factory, mailoutbox
):
    settings.FAKE_SLACK_API = True

    client.force_login(django_user_model.objects.create(role=1))

    to_do_user1 = to_do_user_factory(user__slack_user_id="slackx")

    # not a valid template type
    url = reverse("people:new_hire_remind", args=["todouser1", to_do_user1.id])
    response = client.post(url, follow=True)
    assert response.status_code == 404

    url = reverse("people:new_hire_remind", args=["todouser", to_do_user1.id])

    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert "Reminder has been sent!" in response.content.decode()
    assert len(mailoutbox) == 0

    assert cache.get("slack_channel") == to_do_user1.user.slack_user_id
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Don't forget this item!"},
        },
        {
            "type": "section",
            "block_id": str(to_do_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": "*" + to_do_user1.to_do.name + "*\nThis task has no deadline.",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View details"},
                "style": "primary",
                "value": str(to_do_user1.id),
                "action_id": f"dialog:to_do:{to_do_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_new_hire_remind_resource(
    client, settings, django_user_model, resource_user_factory, mailoutbox
):
    client.force_login(django_user_model.objects.create(role=1))
    resource_user1 = resource_user_factory()

    url = reverse("people:new_hire_remind", args=["resourceuser", resource_user1.id])

    client.post(url, follow=True)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please complete this task"
    assert len(mailoutbox[0].to) == 1
    assert settings.BASE_URL in mailoutbox[0].alternatives[0][0]
    assert resource_user1.resource.name in mailoutbox[0].alternatives[0][0]
    assert resource_user1.user.first_name in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_new_hire_remind_resource_slack_message(
    client, settings, django_user_model, resource_user_factory, mailoutbox
):
    settings.FAKE_SLACK_API = True

    client.force_login(django_user_model.objects.create(role=1))
    resource_user1 = resource_user_factory(user__slack_user_id="slackx")

    url = reverse("people:new_hire_remind", args=["resourceuser", resource_user1.id])

    client.post(url, follow=True)

    assert len(mailoutbox) == 0

    assert cache.get("slack_channel") == resource_user1.user.slack_user_id
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "Don't forget this item!"},
        },
        {
            "type": "section",
            "block_id": str(resource_user1.id),
            "text": {
                "type": "mrkdwn",
                "text": "*" + resource_user1.resource.name + "*",
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "View resource"},
                "style": "primary",
                "value": str(resource_user1.id),
                "action_id": f"dialog:resource:{resource_user1.id}",
            },
        },
    ]


@pytest.mark.django_db
def test_new_hire_tasks(
    client,
    django_user_model,
    resource_factory,
    to_do_factory,
    appointment_factory,
    introduction_factory,
    preboarding_factory,
    new_hire_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    # tasks
    to_do1 = to_do_factory()
    resource1 = resource_factory()
    appointment1 = appointment_factory()
    introduction1 = introduction_factory()
    preboarding1 = preboarding_factory()

    # get the page with items (none yet)
    url = reverse("people:new_hire_tasks", args=[new_hire1.id])

    response = client.get(url)

    # Check if all items are listed
    assert to_do1.name not in response.content.decode()
    assert resource1.name not in response.content.decode()
    assert appointment1.name not in response.content.decode()
    assert introduction1.name not in response.content.decode()
    assert preboarding1.name not in response.content.decode()

    # All are empty
    assert "no preboarding items" in response.content.decode()
    assert "no to do items" in response.content.decode()
    assert "no resource items" in response.content.decode()
    assert "no introduction items" in response.content.decode()
    assert "no appointment items" in response.content.decode()

    # adding all tasks to new hire. One of each
    new_hire1.to_do.add(to_do1)
    new_hire1.resources.add(resource1)
    new_hire1.appointments.add(appointment1)
    new_hire1.introductions.add(introduction1)
    new_hire1.preboarding.add(preboarding1)

    url = reverse("people:new_hire_tasks", args=[new_hire1.id])

    response = client.get(url)

    # All are not empty
    assert "no preboarding items" not in response.content.decode()
    assert "no to do items" not in response.content.decode()
    assert "no resource items" not in response.content.decode()
    assert "no introduction items" not in response.content.decode()
    assert "no appointment items" not in response.content.decode()

    # Check if all items are listed
    assert to_do1.name in response.content.decode()
    assert resource1.name in response.content.decode()
    assert appointment1.name in response.content.decode()
    assert introduction1.name in response.content.decode()
    assert preboarding1.name in response.content.decode()


@pytest.mark.django_db
def test_new_hire_access_list(
    client,
    django_user_model,
    new_hire_factory,
    integration_factory,
    custom_integration_factory,
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()
    # Slack integration - should not show up
    integration1 = integration_factory(integration=0)
    # Should show up
    integration2 = custom_integration_factory(name="Asana", integration=10)

    integration3 = custom_integration_factory(name="Google", integration=10)
    # Remove exists, so should not show up
    integration3.manifest = {}
    integration3.save()

    # Get the page with integrations
    url = reverse("people:new_hire_access", args=[new_hire1.id])

    response = client.get(url)

    assert integration1.name not in response.content.decode()
    assert integration2.name in response.content.decode()
    assert integration3.name not in response.content.decode()


@pytest.mark.django_db
@patch(
    "requests.request",
    Mock(
        return_value=Mock(status_code=201, json=lambda: {"email": "stan@example.com"})
    ),
)
def test_new_hire_access_per_integration(
    client, django_user_model, new_hire_factory, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory(email="stan@example.com")
    new_hire2 = new_hire_factory()
    integration1 = custom_integration_factory(name="Asana", integration=10)

    # New hire already has an account (email matches with return)
    url = reverse(
        "people:new_hire_check_integration", args=[new_hire1.id, integration1.id]
    )

    response = client.get(url)

    assert integration1.name in response.content.decode()
    assert "Activated" in response.content.decode()

    # New hire has no account
    url = reverse(
        "people:new_hire_check_integration", args=[new_hire2.id, integration1.id]
    )

    response = client.get(url)

    assert integration1.name in response.content.decode()
    assert "Give access" in response.content.decode()


@pytest.mark.django_db
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=201,
            json=lambda: {"data": [{"gid": "test_team", "name": "test team"}]},
        )
    ),
)
def test_new_hire_access_per_integration_config_form(
    client, django_user_model, new_hire_factory, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory(email="stan@example.com")
    integration1 = custom_integration_factory(name="Asana", integration=10)

    # New hire already has an account (email matches with return)
    url = reverse(
        "people:new_hire_give_integration", args=[new_hire1.id, integration1.id]
    )
    # Show form to admin
    response = client.get(url)

    # Check that form is present
    assert "Select team to add user to" in response.content.decode()
    assert (
        '<select name="TEAM_ID" class="select form-select" id="id_TEAM_ID"> <option value="test_team">test team</option>'  # noqa
        in response.content.decode()
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory, type, status_code",
    [
        (ToDoFactory, "todo", 200),
        (PreboardingFactory, "preboarding", 200),
        (ResourceFactory, "resource", 200),
        (IntroductionFactory, "introduction", 200),
        (AppointmentFactory, "appointment", 200),
        (AppointmentFactory, "appointment22", 404),
    ],
)
def test_new_hire_tasks_list(
    client, django_user_model, new_hire_factory, factory, type, status_code
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    # tasks
    item1 = factory()
    item2 = factory(template=False)

    # get the page with items
    url = reverse("people:new_hire_task_list", args=[new_hire1.id, type])

    response = client.get(url)

    assert response.status_code == status_code

    if status_code == 200:

        assert item1.name in response.content.decode()

        # only template items are displayed
        assert item2.name not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory, type, status_code",
    [
        (ToDoFactory, "todo", 200),
        (PreboardingFactory, "preboarding", 200),
        (ResourceFactory, "resource", 200),
        (IntroductionFactory, "introduction", 200),
        (AppointmentFactory, "appointment", 200),
        (AppointmentFactory, "appointment22", 404),
    ],
)
def test_new_hire_toggle_tasks(
    client, django_user_model, new_hire_factory, factory, type, status_code
):
    client.force_login(django_user_model.objects.create(role=1))

    new_hire1 = new_hire_factory()

    # Generate template
    item = factory()

    # Post to page to add an item
    url = reverse("people:toggle_new_hire_task", args=[new_hire1.id, item.id, type])
    response = client.post(url, follow=True)

    assert response.status_code == status_code

    if status_code == 200:

        # Get items in specific field for user
        user_items = getattr(new_hire1, get_user_field(type))

        # Should be one now as it was added
        assert user_items.all().count() == 1
        assert "Added" in response.content.decode()

    # Add
    response = client.post(url, follow=True)

    if status_code == 200:

        # Should be removed now
        assert user_items.all().count() == 0
        assert "Add" in response.content.decode()


# COLLEAGUES #


@pytest.mark.django_db
@pytest.mark.parametrize(
    "factory",
    [
        (NewHireFactory),
        (AdminFactory),
        (ManagerFactory),
        (EmployeeFactory),
    ],
)
def test_colleagues_list_all_types_of_users_show(client, django_user_model, factory):
    client.force_login(django_user_model.objects.create(role=1))

    user = factory()

    url = reverse("people:colleagues")
    response = client.get(url)

    assert response.status_code == 200
    assert user.full_name in response.content.decode()


@pytest.mark.django_db
def test_colleague_create(client, django_user_model, department_factory):
    admin_user = django_user_model.objects.create(role=1)
    client.force_login(admin_user)

    # Generate departments to select
    department1 = department_factory()
    department2 = department_factory()

    # Set org default timezone/language
    org = Organization.object.get()
    org.timezone = "Europe/Amsterdam"
    org.language = "nl"
    org.save()

    url = reverse("people:colleague_create")
    response = client.get(url)

    # Check that Amsterdam is selected as default
    assert (
        '<option value="Europe/Amsterdam" selected>Europe/Amsterdam</option>'
        in response.content.decode()
    )
    # Check that Dutch is selected as default
    assert '<option value="nl" selected>Dutch</option>' in response.content.decode()
    assert "First name" in response.content.decode()
    assert "Create new colleague" in response.content.decode()
    assert department1.name in response.content.decode()
    assert department2.name in response.content.decode()

    # Create a colleague
    response = client.post(
        url,
        data={
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "timezone": "Europe/Amsterdam",
            "language": "nl",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert django_user_model.objects.count() == 2
    assert "Colleague has been added" in response.content.decode()

    # Shows up on colleagues page
    url = reverse("people:colleagues")
    response = client.get(url)

    assert "stan@chiefonboarding.com" in response.content.decode()

    # Try posting again with same email
    url = reverse("people:colleague_create")
    response = client.post(
        url,
        data={
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "timezone": "Europe/Amsterdam",
            "language": "nl",
        },
        follow=True,
    )

    assert "Colleague has been added" not in response.content.decode()
    assert "already exists" in response.content.decode()


@pytest.mark.django_db
def test_colleague_update(client, django_user_model):
    admin_user = django_user_model.objects.create(
        first_name="John",
        last_name="Do",
        email="john@chiefonboarding.com",
        language="en",
        timezone="Europe/Amsterdam",
        role=1,
    )
    client.force_login(admin_user)

    url = reverse("people:colleague", args=[admin_user.id])
    response = client.get(url)

    # Check that fiels are shown correctly based on user
    assert admin_user.first_name in response.content.decode()
    assert admin_user.last_name in response.content.decode()
    assert admin_user.email in response.content.decode()
    assert (
        '<option value="Europe/Amsterdam" selected>Europe/Amsterdam</option>'
        in response.content.decode()
    )
    assert '<option value="en" selected>English</option>' in response.content.decode()
    assert "Resources available" in response.content.decode()
    assert "No resources are available to this user yet" in response.content.decode()
    assert "Change" in response.content.decode()

    # Try updating user
    response = client.post(
        url,
        data={
            "id": admin_user.id,
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "timezone": "UTC",
            "language": "en",
        },
        follow=True,
    )

    assert response.status_code == 200
    assert django_user_model.objects.count() == 1
    assert "Employee has been updated" in response.content.decode()

    # Try updating user (different language)
    response = client.post(
        url,
        data={
            "id": admin_user.id,
            "first_name": "Stan",
            "last_name": "Do",
            "email": "stan@chiefonboarding.com",
            "timezone": "UTC",
            "language": "nl",
        },
        follow=True,
    )

    # Updated user details are shown
    assert "Stan" in response.content.decode()
    assert "Do" in response.content.decode()
    assert "stan@chiefonboarding.com" in response.content.decode()
    assert '<option value="UTC" selected>UTC</option>' in response.content.decode()
    assert (
        '<option value="nl" selected>Nederlands</option>' in response.content.decode()
    )


@pytest.mark.django_db
def test_colleague_delete(client, django_user_model, new_hire_factory):
    admin_user = django_user_model.objects.create(role=1)
    client.force_login(admin_user)

    new_hire1 = new_hire_factory()

    assert django_user_model.objects.all().count() == 2

    url = reverse("people:colleague_delete", args=[new_hire1.id])
    response = client.post(url, follow=True)

    assert "Colleague has been removed" in response.content.decode()
    assert new_hire1.full_name not in response.content.decode()
    assert django_user_model.objects.all().count() == 1


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.get_all_users",
    Mock(
        return_value=[
            {
                "id": "W01234DE",
                "team_id": "T012344",
                "name": "John",
                "deleted": False,
                "color": "9f6349",
                "real_name": "Do",
                "tz": "UTC",
                "tz_label": "UTC",
                "tz_offset": -2000,
                "profile": {
                    "avatar_hash": "34343",
                    "status_text": "Ready!",
                    "status_emoji": ":+1:",
                    "real_name": "John Do",
                    "display_name": "johndo",
                    "real_name_normalized": "John Do",
                    "display_name_normalized": "johndo",
                    "email": "john@chiefonboarding.com",
                    "team": "T012AB4",
                },
                "is_admin": True,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": False,
                "updated": 1502138634,
                "is_app_user": False,
                "has_2fa": False,
            },
            {
                "id": "USLACKBOT",
                "team_id": "T012344",
                "name": "Bot",
                "deleted": False,
                "color": "9f6349",
                "real_name": "Do",
                "tz": "UTC",
                "tz_label": "UTC",
                "tz_offset": -2000,
                "profile": {
                    "avatar_hash": "34343",
                    "status_text": "Ready!",
                    "status_emoji": ":+1:",
                    "real_name": "Slack bot",
                    "display_name": "slack bot",
                    "real_name_normalized": "Slack bot",
                    "display_name_normalized": "slack bot",
                    "team": "T012AB4",
                },
                "is_admin": True,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": False,
                "updated": 1502138634,
                "is_app_user": False,
                "has_2fa": False,
            },
            {
                "id": "W07Q343A4",
                "team_id": "T0G334BBK",
                "name": "Stan",
                "deleted": False,
                "color": "9f34e7",
                "real_name": "Stan Do",
                "tz": "America/Los_Angeles",
                "tz_label": "Pacific Daylight Time",
                "tz_offset": -25200,
                "profile": {
                    "avatar_hash": "klsdksdlkf",
                    "first_name": "Stan",
                    "last_name": "Do",
                    "title": "The chief",
                    "phone": "122433",
                    "skype": "",
                    "real_name": "Stan Do",
                    "real_name_normalized": "Stan Do",
                    "display_name": "Stan Do",
                    "display_name_normalized": "Stan Do",
                    "email": "stan@chiefonboarding.com",
                },
                "is_admin": True,
                "is_owner": False,
                "is_primary_owner": False,
                "is_restricted": False,
                "is_ultra_restricted": False,
                "is_bot": False,
                "updated": 2343444,
                "has_2fa": False,
            },
        ],
    ),
)
def test_import_users_from_slack(client, django_user_model):
    from admin.integrations.models import Integration

    Integration.objects.create(integration=0)
    admin_user = django_user_model.objects.create(role=1)
    client.force_login(admin_user)

    url = reverse("people:sync-slack")
    response = client.get(url)

    # Get colleagues list (triggered through HTMX)
    url = reverse("people:colleagues")
    response = client.get(url)

    # 1 admin + two imported users
    assert django_user_model.objects.all().count() == 3
    assert response.status_code == 200
    assert "Stan" in response.content.decode()
    assert "John" in response.content.decode()


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.find_by_email", Mock(return_value={"user": {"id": "slackx"}})
)
def test_give_user_slack_access(settings, client, employee_factory, django_user_model):
    settings.FAKE_SLACK_API = True

    employee_with_slack = employee_factory(slack_user_id="slackx")
    employee_without_slack = employee_factory()
    admin_user = django_user_model.objects.create(role=1)
    client.force_login(admin_user)

    assert employee_with_slack.has_slack_account
    url = reverse("people:connect-to-slack", args=[employee_with_slack.id])
    response = client.post(url)

    employee_with_slack.refresh_from_db()
    assert "Give access" in response.content.decode()
    assert not employee_with_slack.has_slack_account

    assert not employee_without_slack.has_slack_account
    url = reverse("people:connect-to-slack", args=[employee_without_slack.id])
    response = client.post(url)

    # New hire has now Slack access and message has been sent
    employee_without_slack.refresh_from_db()
    assert employee_without_slack.has_slack_account
    assert employee_without_slack.slack_user_id == "slackx"
    assert "Revoke Slack access" in response.content.decode()

    assert cache.get("slack_channel") == employee_without_slack.slack_user_id
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Click on the button to see all the categories that "
                "are available to you!",
            },
        },
        {
            "type": "actions",
            "elements": {
                "type": "button",
                "text": {"type": "plain_text", "text": "resources"},
                "style": "primary",
                "value": "show:resources",
                "action_id": "show:resources",
            },
        },
    ]


@pytest.mark.django_db
@patch("slack_bot.utils.Slack.find_by_email", Mock(return_value=False))
def test_give_user_slack_access_does_not_exist(
    settings, client, employee_factory, django_user_model
):
    settings.FAKE_SLACK_API = True

    employee_without_slack = employee_factory()
    admin_user = django_user_model.objects.create(role=1)
    client.force_login(admin_user)

    assert not employee_without_slack.has_slack_account
    url = reverse("people:connect-to-slack", args=[employee_without_slack.id])
    response = client.post(url)

    employee_without_slack.refresh_from_db()
    assert "Could not find user" in response.content.decode()
    assert not employee_without_slack.has_slack_account


@pytest.mark.django_db
@pytest.mark.parametrize(
    "user_factory, status_code",
    [
        (NewHireFactory, 404),
        (AdminFactory, 404),
        (ManagerFactory, 404),
        (EmployeeFactory, 200),
    ],
)
def test_employee_toggle_portal_access(
    client, django_user_model, user_factory, status_code, mailoutbox
):
    client.force_login(django_user_model.objects.create(role=1))

    employee1 = user_factory()

    url = reverse("people:colleagues")
    response = client.get(url)

    # User is displayed on colleagues page and also slack button
    assert employee1.full_name in response.content.decode()
    # Slack is not enabled
    assert "slack" not in response.content.decode()

    # Enable portal access
    url = reverse("people:toggle-portal-access", args=[employee1.id])
    response = client.post(url)

    # Should only work for employees, not newhires/admins etc
    assert response.status_code == status_code

    # Skip the 404's
    if status_code == 200:

        # Get the object again
        employee1.refresh_from_db()

        # Now employee is active
        assert employee1.is_active
        # Button flipped
        assert "Revoke access" in response.content.decode()

        # Email has been sent to new hire
        assert response.status_code == 200
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Your login credentials!"
        assert employee1.email in mailoutbox[0].alternatives[0][0]
        assert len(mailoutbox[0].to) == 1
        assert mailoutbox[0].to[0] == employee1.email

        # Enable portal access
        url = reverse("people:toggle-portal-access", args=[employee1.id])
        response = client.post(url)

        # Get the object again
        employee1.refresh_from_db()

        # Now employee is not active
        assert not employee1.is_active

        # Button flipped
        assert "Revoke access" not in response.content.decode()
        assert "Give access" in response.content.decode()


@pytest.mark.django_db
def test_employee_can_only_login_with_access(
    client, django_user_model, employee_factory
):
    employee1 = employee_factory()

    url = reverse("login")
    data = {"username": employee1.email, "password": "test"}
    client.post(url, data=data, follow=True)

    user = auth.get_user(client)
    assert not user.is_authenticated

    # Enable portal access
    client.force_login(django_user_model.objects.create(role=1))
    url = reverse("people:toggle-portal-access", args=[employee1.id])
    client.post(url)
    client.logout()

    employee1.refresh_from_db()
    # Force change employee password
    employee1.set_password("test")
    employee1.save()

    # Check that admin user is logged out
    assert not user.is_authenticated

    # Try logging in again with employee account
    url = reverse("login")
    client.post(url, data=data, follow=True)

    user = auth.get_user(client)
    assert user.is_authenticated


@pytest.mark.django_db
def test_employee_resources(
    client, django_user_model, employee_factory, resource_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    employee1 = employee_factory()
    resource1 = resource_factory()
    resource2 = resource_factory(template=False)

    url = reverse("people:add_resource", args=[employee1.id])
    response = client.get(url, follow=True)

    assert resource1.name in response.content.decode()
    # Only show templates
    assert resource2.name not in response.content.decode()
    assert "Added" not in response.content.decode()

    # Add resource to user
    employee1.resources.add(resource1)

    response = client.get(url, follow=True)

    # Has been added, so change button name
    assert resource2.name not in response.content.decode()
    assert "Added" in response.content.decode()


@pytest.mark.django_db
def test_employee_toggle_resources(
    client, django_user_model, employee_factory, resource_factory
):
    client.force_login(django_user_model.objects.create(role=1))

    resource1 = resource_factory()
    employee1 = employee_factory()

    url = reverse("people:toggle_resource", args=[employee1.id, resource1.id])
    response = client.post(url, follow=True)

    assert "Added" in response.content.decode()
    assert employee1.resources.filter(id=resource1.id).exists()

    # Now remove the item
    response = client.post(url, follow=True)

    assert "Add" in response.content.decode()
    assert not employee1.resources.filter(id=resource1.id).exists()
