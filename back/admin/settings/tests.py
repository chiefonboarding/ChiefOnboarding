from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from admin.integrations.models import Integration
from organization.models import Notification, Organization
from slack_bot.models import SlackChannel


@pytest.mark.django_db
def test_update_org_settings(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

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
def test_update_org_settings_min_one_login_method(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("settings:general")
    response = client.get(url)

    # Google login is not available
    assert "Google account" not in response.content.decode()

    data = {
        "name": "test",
        "language": "en",
        "timezone": "UTC",
        "base_color": "#FFFFF",
        "accent_color": "#FFFFF",
        "credentials_login": False,
    }

    response = client.post(url, data=data, follow=True)

    org = Organization.object.get()

    # Did not update
    assert org.credentials_login
    assert "You must enable at least one login option" in response.content.decode()

    # Create Google login integration
    Integration.objects.create(integration=3)

    response = client.get(url)
    # Google login is  available
    assert "Google" in response.content.decode()

    data = {
        "name": "test",
        "language": "en",
        "timezone": "UTC",
        "base_color": "#FFFFF",
        "accent_color": "#FFFFF",
        "credentials_login": False,
        "google_login": True,
    }
    response = client.post(url, data=data, follow=True)

    org.refresh_from_db()

    assert "You must enable at least one login option" not in response.content.decode()
    assert not org.credentials_login
    assert org.google_login


@pytest.mark.django_db
def test_update_org_slack_settings(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("settings:slack")
    response = client.get(url)

    assert "#ffbb42" in response.content.decode()

    data = {
        "bot_color": "#FFFFFF",
    }

    response = client.post(url, data=data, follow=True)

    assert "#FFFFFF" in response.content.decode()


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
    assert Notification.objects.all().count() == 1
    assert Notification.objects.first().notification_type == "added_administrator"

    # Try to create the same user now, but as a manager
    data = {
        "first_name": "Stan",
        "last_name": "Do",
        "email": "STAn@chiefonboarding.com",
        "role": 2,
    }
    response = client.post(url, data=data, follow=True)

    assert "Admin/Manager has been created" in response.content.decode()
    assert Notification.objects.all().count() == 2
    assert Notification.objects.first().notification_type == "added_manager"
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
        print(language[1])
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
    print(response.content.decode())

    admin_user1.refresh_from_db()

    assert "Selecteer een geldige keuze." in response.content.decode()
    assert admin_user1.language == "nl"
    assert response.status_code == 200


@pytest.mark.django_db
def test_otp_view(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)

    url = reverse("settings:personal-otp")
    response = client.get(url)

    assert "Please scan the code below" in response.content.decode()

    # Secret is necessary to set up TOTP
    assert admin_user1.totp_secret in response.content.decode()
    assert "6 digit OTP code" in response.content.decode()


@pytest.mark.django_db
@patch("pyotp.TOTP.verify", Mock(return_value=False))
def test_enable_otp_view_wrong_otp(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)

    url = reverse("settings:personal-otp")
    response = client.post(url, {"otp": 223456}, follow=True)

    admin_user1.refresh_from_db()

    assert not admin_user1.requires_otp
    assert "OTP token was not correct." in response.content.decode()


@pytest.mark.django_db
@patch("pyotp.TOTP.verify", Mock(return_value=True))
def test_enable_otp_view_correct_otp(client, admin_factory):
    admin_user1 = admin_factory()
    client.force_login(admin_user1)

    url = reverse("settings:personal-otp")
    response = client.post(url, {"otp": 223456}, follow=True)

    admin_user1.refresh_from_db()

    assert "Please copy and save the keys below. These will only show once"
    assert len(response.context["keys"]) == 10
    assert admin_user1.requires_otp
    assert "OTP token was not correct." not in response.content.decode()

    response = client.get(url)

    assert "OTP has been enabled for your account" not in response.content.decode()


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

    Integration.objects.create(integration=0)

    response = client.get(url)

    assert "Remove" in response.content.decode()
    assert "Update Slack channels list" in response.content.decode()

    integration = Integration.objects.create(integration=10, name="Test integration")

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
    Integration.objects.create(integration=0)

    url = reverse("settings:slack-account-update-channels")
    response = client.get(url)

    assert "Newly added channels have been added." not in response.content.decode()
    assert SlackChannel.objects.all().count() == 3
    assert SlackChannel.objects.filter(name="general", is_private=False).exists()
