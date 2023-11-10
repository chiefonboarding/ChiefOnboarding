from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from django_q.models import Schedule

from admin.integrations.models import Integration
from organization.models import Notification, WelcomeMessage
from slack_bot.models import SlackChannel


@pytest.mark.django_db
def test_update_org_settings(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("settings:general")
    response = client.get(url)

    assert "General Updates" in response.content.decode()

    # try updating
    data = {
        "name": "Chief123",
        "language": "en",
        "timezone": "Europe/Amsterdam",
        "base_color": "#FFFFFF",
        "accent_color": "#FFFFF",
        "credentials_login": True,
    }

    response = client.post(url, data=data, follow=True)

    assert "Organization info has been updated" in response.content.decode()
    assert "Chief123" in response.content.decode()
    assert "English" in response.content.decode()
    assert "Europe/Amsterdam" in response.content.decode()
    assert "#FFFFFF" in response.content.decode()


@pytest.mark.django_db
def test_update_org_slack_settings(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("settings:slack")
    response = client.get(url)

    assert "#ffbb42" in response.content.decode()

    data = {
        "bot_color": "#FFFFFF",
    }

    response = client.post(url, data=data, follow=True)

    assert "#FFFFFF" in response.content.decode()


@pytest.mark.django_db
def test_update_org_slack_birthday(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("settings:slack")

    data = {
        "slack_birthday_wishes_channel": 1,
        "slack_default_channel": 1,
        "bot_color": "#FFFFFF",
    }

    client.post(url, data=data, follow=True)

    assert Schedule.objects.filter(name="birthday_reminder").exists()

    data = {
        "slack_birthday_wishes_channel": "",
        "slack_default_channel": 1,
        "bot_color": "#FFFFFF",
    }

    client.post(url, data=data, follow=True)

    assert not Schedule.objects.filter(name="birthday_reminder").exists()


@pytest.mark.django_db
def test_update_welcome_message(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("settings:welcome-message", args=["en", 1])
    response = client.get(url)

    response = client.post(url, data={"message": "Updated item"}, follow=True)

    assert "Message has been updated" in response.content.decode()
    assert "Updated item" in response.content.decode()

    # Check that all languages are listed
    for language in settings.LANGUAGES:
        assert str(language[1]) in response.content.decode()


@pytest.mark.django_db
def test_administrator_settings_view(client, admin_factory):
    admin_user = admin_factory()
    client.force_login(admin_user)

    url = reverse("settings:administrators")
    response = client.get(url)

    assert admin_user.full_name in response.content.decode()
    assert admin_user.email in response.content.decode()
    assert "Change" in response.content.decode()

    # Delete button not available for our own account
    assert "Delete" not in response.content.decode()

    # Create another admin
    admin_user = admin_factory()

    response = client.get(url)

    assert admin_user.full_name in response.content.decode()
    assert admin_user.email in response.content.decode()
    assert "Change" in response.content.decode()
    # Can delete the other one
    assert "Delete" in response.content.decode()


@pytest.mark.django_db
def test_administrator_settings_cannot_delete_own_account(client, admin_factory):
    admin_user1 = admin_factory()
    admin_factory()

    client.force_login(admin_user1)

    url = reverse("settings:administrators-delete", args=[admin_user1.id])
    response = client.post(url)

    assert response.status_code == 404
    assert get_user_model().objects.all().count() == 2


@pytest.mark.django_db
def test_administrator_settings_delete_other_account(client, admin_factory):
    admin_user1 = admin_factory()
    admin_user2 = admin_factory()

    client.force_login(admin_user1)

    url = reverse("settings:administrators-delete", args=[admin_user2.id])
    response = client.post(url, follow=True)

    assert response.status_code == 200
    assert get_user_model().objects.all().count() == 2
    assert get_user_model().admins.all().count() == 1
    assert get_user_model().managers_and_admins.all().count() == 1
    assert "Delete" not in response.content.decode()


@pytest.mark.django_db
def test_create_administrator(client, admin_factory, mailoutbox):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)
    url = reverse("settings:administrators-create")

    response = client.get(url)
    # Only show admin/manager options
    assert "Administrator" in response.content.decode()
    assert "Manager" in response.content.decode()
    assert "Other" not in response.content.decode()
    assert "New Hire" not in response.content.decode()

    data = {
        "first_name": "Stan",
        "last_name": "Do",
        "email": "stan@chiefonboarding.com",
        "role": 1,
    }
    response = client.post(url, data=data, follow=True)

    new_admin_user = get_user_model().objects.get(email="stan@chiefonboarding.com")

    # Test sending out email
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Your login credentials!"
    assert new_admin_user.email in mailoutbox[0].alternatives[0][0]
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == new_admin_user.email

    assert "Admin/Manager has been created" in response.content.decode()
    assert get_user_model().admins.all().count() == 2
    assert Notification.objects.all().count() == 2
    assert (
        Notification.objects.first().notification_type == Notification.Type.ADDED_ADMIN
    )

    # Try to create the same user now, but as a manager
    data = {
        "first_name": "Stan",
        "last_name": "Do",
        "email": "STAn@chiefonboarding.com",
        "role": 2,
    }
    response = client.post(url, data=data, follow=True)

    assert "Admin/Manager has been created" in response.content.decode()
    assert Notification.objects.all().count() == 3
    assert (
        Notification.objects.first().notification_type
        == Notification.Type.ADDED_MANAGER
    )
    # Amount of admins stays 2 as it will overwrite the previous one
    assert get_user_model().managers_and_admins.all().count() == 2


@pytest.mark.django_db
def test_change_administrator(client, admin_factory, new_hire_factory):
    admin_user1 = admin_factory()
    admin_user2 = admin_factory()
    new_hire1 = new_hire_factory()
    client.force_login(admin_user1)

    url = reverse("settings:administrators-update", args=[admin_user2.id])
    response = client.get(url)

    # Only show admin/manager options
    assert "Administrator" in response.content.decode()
    assert "Manager" in response.content.decode()
    assert "Other" not in response.content.decode()
    assert "New Hire" not in response.content.decode()

    response = client.post(url, data={"role": 2}, follow=True)

    assert get_user_model().new_hires.all().count() == 1
    assert get_user_model().admins.all().count() == 1
    assert get_user_model().managers_and_admins.all().count() == 2

    assert "Admin/Manager has been changed" in response.content.decode()

    # Cannot update role of new hire
    url = reverse("settings:administrators-update", args=[new_hire1.id])
    response = client.post(url, data={"role": 1}, follow=True)

    assert response.status_code == 404
    assert get_user_model().new_hires.all().count() == 1
    assert get_user_model().managers_and_admins.all().count() == 2


@pytest.mark.django_db
def test_language_view(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)

    url = reverse("settings:personal-language")
    response = client.get(url)

    assert response.status_code == 200
    assert "Language" in response.content.decode()
    # English is selected by default (based on ORG)
    assert '<option value="en" selected>English</option>' in response.content.decode()

    # Check that all languages are listed
    for language in settings.LANGUAGES:
        assert str(language[1]) in response.content.decode()


@pytest.mark.django_db
def test_language_update(client, admin_factory):
    admin_user1 = admin_factory(language="en")
    client.force_login(admin_user1)

    url = reverse("settings:personal-language")
    response = client.post(url, {"language": "nl"}, follow=True)

    admin_user1.refresh_from_db()

    assert response.status_code == 200
    assert "Taal" in response.content.decode()
    # Now Dutch is selected
    assert (
        '<option value="nl" selected>Nederlands</option>' in response.content.decode()
    )
    assert admin_user1.language == "nl"

    # Try updating with language that does not exist
    url = reverse("settings:personal-language")
    response = client.post(url, {"language": "nli34"}, follow=True)

    admin_user1.refresh_from_db()

    assert "Selecteer een geldige keuze." in response.content.decode()
    assert admin_user1.language == "nl"
    assert response.status_code == 200


@pytest.mark.django_db
def test_sending_test_preboarding_message(
    client, admin_factory, mailoutbox, welcome_message_factory
):
    admin = admin_factory()
    client.force_login(admin)

    welcome_message_factory(
        message_type=WelcomeMessage.Type.PREBOARDING,
        language="es",
        message="Spanish test message {{ first_name }}",
    )
    url = reverse("settings:welcome-message-test-message", args=["es", 0])

    client.post(url)

    # Sent the test mail to admin
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to[0] == admin.email
    assert admin.first_name in mailoutbox[0].alternatives[0][0]
    assert "Spanish" in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_sending_test_credentials_message(
    client, admin_factory, mailoutbox, welcome_message_factory
):
    admin = admin_factory()
    client.force_login(admin)

    welcome_message_factory(
        message_type=WelcomeMessage.Type.NEWHIRE_WELCOME,
        language="es",
        message="Spanish test message {{ first_name }}",
    )
    url = reverse("settings:welcome-message-test-message", args=["es", 1])

    client.post(url)

    # Sent the test mail to admin
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to[0] == admin.email
    assert admin.first_name in mailoutbox[0].alternatives[0][0]
    assert "Spanish" in mailoutbox[0].alternatives[0][0]
    assert "FAKEPASSWORD" in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_sending_test_new_hire_welcome_message(
    client, admin_factory, welcome_message_factory
):
    admin = admin_factory(slack_user_id="slackx")
    client.force_login(admin)

    welcome_message_factory(
        message_type=WelcomeMessage.Type.SLACK_WELCOME,
        language="es",
        message="Spanish test message {{ first_name }}",
    )
    url = reverse("settings:welcome-message-test-message", args=["es", 3])

    client.post(url)

    assert cache.get("slack_channel", "") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "Spanish test message " + admin.first_name,
            },
        },
    ]


@pytest.mark.django_db
def test_sending_test_colleague_welcome_message(
    client, admin_factory, welcome_message_factory
):
    admin = admin_factory(slack_user_id="slackx")
    client.force_login(admin)

    welcome_message_factory(
        message_type=WelcomeMessage.Type.SLACK_KNOWLEDGE,
        language="es",
        message="Spanish test message {{ first_name }}",
    )
    url = reverse("settings:welcome-message-test-message", args=["es", 4])

    client.post(url)

    assert cache.get("slack_channel", "") == "slackx"
    assert cache.get("slack_blocks") == [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Spanish test message {admin.first_name}",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "recursos"},
                    "style": "primary",
                    "value": "show_resource_items",
                    "action_id": "show_resource_items",
                },
            ],
        },
    ]


@pytest.mark.django_db
def test_integration_list(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)

    url = reverse("settings:integrations")
    response = client.get(url)

    assert "Integrations" in response.content.decode()
    assert "Slack bot" in response.content.decode()
    assert "No custom integrations yet" in response.content.decode()
    assert "Enable" in response.content.decode()
    assert "Remove" not in response.content.decode()
    assert "Update Slack channels list" not in response.content.decode()

    Integration.objects.create(integration=Integration.Type.SLACK_BOT)

    response = client.get(url)

    assert "Remove" in response.content.decode()
    assert "Update Slack channels list" in response.content.decode()

    integration = Integration.objects.create(
        integration=Integration.Type.CUSTOM, name="Test integration"
    )

    response = client.get(url)

    assert "No custom integrations yet" not in response.content.decode()
    assert integration.name in response.content.decode()


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.get_channels",
    Mock(
        return_value=[
            ["general", False],
            ["introductions", False],
            ["somethingprivate", True],
        ]
    ),
)
def test_slack_channels_update_view(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)
    Integration.objects.create(integration=Integration.Type.SLACK_BOT)

    url = reverse("settings:slack-account-update-channels")
    response = client.get(url)

    assert "Newly added channels have been added." not in response.content.decode()
    assert SlackChannel.objects.all().count() == 3
    assert SlackChannel.objects.filter(name="general", is_private=False).exists()
