import pytest
from django.urls import reverse

from admin.preboarding.factories import PreboardingFactory
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
    print(response.content.decode())
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
