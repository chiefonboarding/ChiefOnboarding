from unittest.mock import Mock, patch

import pytest
from django.urls import reverse

from admin.integrations.models import Integration


@pytest.mark.django_db
def test_create_integration(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("integrations:create")
    response = client.get(url)

    assert "Add new integration" in response.content.decode()

    # Post with invalid JSON
    response = client.post(url, {"name": "test", "manifest": '{"test": "Test",}'})

    assert "Enter a valid JSON." in response.content.decode()

    # Post with valid JSON
    response = client.post(url, {"name": "test", "manifest": '{"execute": []}'})

    assert "Enter a valid JSON." not in response.content.decode()
    assert Integration.objects.filter(integration=10).count() == 1


@pytest.mark.django_db
def test_update_integration(client, django_user_model, custom_integration_factory):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    url = reverse("integrations:update", args=[integration.id])
    response = client.get(url)

    assert "Add new integration" in response.content.decode()
    assert "TEAM_ID" in response.content.decode()
    assert integration.name in response.content.decode()


@pytest.mark.django_db
def test_create_google_login_integration(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("integrations:create-google")
    response = client.get(url)

    assert "client_id" in response.content.decode()
    assert "client_secret" in response.content.decode()

    response = client.post(url, data={"client_id": "12", "client_secret": "233"})

    assert Integration.objects.filter(integration=3).count() == 1


@pytest.mark.django_db
def test_delete_integration(client, django_user_model, custom_integration_factory):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    assert Integration.objects.filter(integration=10).count() == 1

    url = reverse("integrations:delete", args=[integration.id])
    response = client.get(url, follow=True)

    assert (
        "Are you sure you want to remove this integration?" in response.content.decode()
    )

    response = client.delete(url, follow=True)

    assert reverse("settings:integrations") in response.redirect_chain[-1][0]
    assert Integration.objects.filter(integration=10).count() == 0


@pytest.mark.django_db
def test_integration_extra_args_form(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory()

    url = reverse("integrations:update-creds", args=[integration.id])
    response = client.get(url)

    assert "Please put your token here" in response.content.decode()
    assert "Organization id" in response.content.decode()
    assert 'name="ORG"' in response.content.decode()
    assert 'name="TOKEN"' in response.content.decode()

    response = client.post(
        url, {"ORG": "123", "TOKEN": "SECRET_TOKEN", "NOTWORKING": "False"}, follow=True
    )

    integration = Integration.objects.first()
    assert integration.extra_args["ORG"] == "123"
    assert integration.extra_args["TOKEN"] == "SECRET_TOKEN"
    assert "NOTWORKING" not in integration.extra_args


@pytest.mark.django_db
def test_integration_oauth_redirect_view(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={"oauth": {"authenticate_url": "http://localhost:8000/test/{{TEST}}"}},
        extra_args={"TEST": "HI"},
    )

    url = reverse("integrations:oauth", args=[integration.id])
    response = client.get(url, follow=True)

    last_url, status_code = response.redirect_chain[-1]

    assert status_code == 302
    assert last_url == "http://localhost:8000/test/HI"

    integration.enabled_oauth = True
    integration.save()

    response = client.get(url, follow=True)

    assert response.status_code == 404


@pytest.mark.django_db
def test_integration_oauth_callback_redirect_view_disabled_when_done(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={"oauth": {"authenticate_url": "http://localhost:8000/test/"}},
        enabled_oauth=True,
    )

    url = reverse("integrations:oauth-callback", args=[integration.id])
    response = client.get(url, follow=True)

    assert response.status_code == 404


@pytest.mark.django_db
def test_integration_oauth_callback_view_redirect_without_code(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={"oauth": {"authenticate_url": "http://localhost:8000/test/"}}
    )

    url = reverse("integrations:oauth-callback", args=[integration.id])
    response = client.get(url, follow=True)

    assert "Code was not provided" in response.content.decode()


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"access_token": "test"}))),
)
def test_integration_oauth_callback_view(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={
            "oauth": {
                "access_token": {"url": "http://localhost:8000/test/"},
                "authenticate_url": "http://localhost:8000/test/",
            }
        }
    )

    url = reverse("integrations:oauth-callback", args=[integration.id])
    client.get(url + "?code=test", follow=True)

    integration.refresh_from_db()
    assert integration.enabled_oauth
    assert integration.extra_args["oauth"] == {"access_token": "test"}


@pytest.mark.django_db
@patch(
    "requests.get",
    Mock(
        return_value=Mock(
            status_code=200,
            text='{"access_token":"vgn", "ok": true, "bot_user_id":"bot"}',
        )
    ),
)
def test_slack_connect(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))
    # Google login is disabled, so url doesn't work
    url = reverse("integrations:slack")
    response = client.get(url, follow=True)

    # No code available
    assert response.status_code == 200
    assert "Could not optain slack authentication code." in response.content.decode()

    response = client.get(url + "?code=test", follow=True)

    assert response.status_code == 200

    assert Integration.objects.filter(integration=0).exists()
    assert "Slack has successfully been connected." in response.content.decode()
