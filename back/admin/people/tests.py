import pytest
from django.urls import reverse

from admin.admin_tasks.factories import *  # noqa
from admin.notes.factories import *  # noqa
from admin.notes.models import Note
from admin.preboarding.factories import PreboardingFactory
from misc.models import File
from organization.factories import NotificationFactory
from organization.models import Organization, WelcomeMessage
from users.factories import *  # noqa


@pytest.mark.django_db
def test_new_hire_list_view(client, new_hire_factory, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    # create 20 new hires
    new_hire_factory.create_batch(20)

    url = reverse("people:new_hires")
    response = client.get(url)

    assert "New hires" in response.content.decode()

    # Number 10 should be listed, number 11 should be on the other page
    # 0 based email address
    assert "fake_new_hire_9" in response.content.decode()
    assert "fake_new_hire_10" not in response.content.decode()

    # Check if pagination works
    assert "last" in response.content.decode()


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

    # Should not appear as it's not public for new hire
    assert not2.extra_text not in response.content.decode()
    assert not2.get_notification_type_display() not in response.content.decode()

    # Should not appear as it's not for this new hire
    assert not3.extra_text not in response.content.decode()
    assert not3.get_notification_type_display() not in response.content.decode()


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
    preboarding = PreboardingFactory()
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
    assert new_hire1.first_name in mailoutbox[0].body
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


# @pytest.mark.django_db
# def test_add_sequence_to_new_hire(
#     client, new_hire_factory, django_user_model
# ):
#     # TODO
#     pass

# @pytest.mark.django_db
# def test_trigger_condition_new_hire(
#     client, new_hire_factory, django_user_model
# ):
#     # TODO
#     pass


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
def test_new_hire_reopen(
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

    # TODO: test slack message


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
