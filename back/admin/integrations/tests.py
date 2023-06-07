import base64
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.urls import reverse
from django.utils import timezone

from admin.integrations.models import Integration
from organization.models import Notification


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
    assert '"hidden" name="PASSWORD"' in response.content.decode()

    response = client.post(
        url, {"ORG": "123", "TOKEN": "SECRET_TOKEN", "NOTWORKING": "False"}, follow=True
    )

    integration = Integration.objects.first()
    assert integration.extra_args["ORG"] == "123"
    assert integration.extra_args["TOKEN"] == "SECRET_TOKEN"
    assert "NOTWORKING" not in integration.extra_args

    response = client.get(url)

    # Value that got added is now shown
    assert "123" in response.content.decode()


@pytest.mark.django_db
def test_integration_request_exceptions_invalid_url(custom_integration_factory):
    integration = custom_integration_factory(
        manifest={
            "oauth": {
                "access_token": {"url": "http://localhost:8000/test/"},
                "authenticate_url": "http://localhost:8000/test/",
            },
            "headers": {},
        }
    )

    success, result = integration.run_request(
        {"method": "POST", "url": "//localhost:8000/test/", "cast_data_to_json": False}
    )

    assert not success
    assert result == "The url is invalid"


@pytest.mark.django_db
def test_integration_request_basic_auth(custom_integration_factory):
    integration = custom_integration_factory(
        manifest={
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Basic {{ADMIN_EMAIL}}:{{TOKEN}}",
            },
            "initial_data_form": [
                {
                    "id": "ADMIN_EMAIL",
                    "name": "The admin email here with which the token was generated.",
                    "description": "",
                },
                {"id": "TOKEN", "name": "The token", "description": ""},
            ],
        }
    )

    integration.params = {"ADMIN_EMAIL": "test@chiefonboarding.com", "TOKEN": "123"}
    assert (
        base64.b64encode("test@chiefonboarding.com:123".encode("ascii")).decode("ascii")
        == "dGVzdEBjaGllZm9uYm9hcmRpbmcuY29tOjEyMw=="
    )
    assert integration.headers() == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdEBjaGllZm9uYm9hcmRpbmcuY29tOjEyMw==",
    }


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
def test_integration_user_exists(
    client, django_user_model, new_hire_factory, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={
            "exists": {
                "url": "http://localhost:8000/test",
                "method": "GET",
                "expected": "{{ email}}",
            }
        }
    )
    new_hire = new_hire_factory()

    # Didn't find user
    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(return_value=(True, Mock(text="[{'error': 'not_found'}]"))),
    ):
        exists = integration.user_exists(new_hire)
        assert not exists

    # Found user
    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(return_value=(True, Mock(text="[{'user': '" + new_hire.email + "'}]"))),
    ):
        exists = integration.user_exists(new_hire)
        assert exists

    # Error went wrong
    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(return_value=(False, Mock(text="[{'user': '" + new_hire.email + "'}]"))),
    ):
        exists = integration.user_exists(new_hire)
        assert exists is None


@pytest.mark.django_db
def test_integration_refresh_token(
    client, django_user_model, new_hire_factory, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={
            "oauth": {
                "refresh": {"url": "http://localhost:8000/test", "method": "GET"}
            },
            "initial_data_form": [],
            "execute": [],
        },
        extra_args={
            "oauth": {
                "expires_in": 500,
            }
        },
        expiring=timezone.now() - timedelta(days=1),
    )
    new_hire = new_hire_factory()

    # This one fails as it couldn't fetch the new token
    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(return_value=(False, Mock(text="[{'error': 'not_found'}]"))),
    ):
        integration.new_hire = new_hire
        integration.renew_key()

        assert (
            Notification.objects.filter(notification_type="failed_integration").count()
            == 1
        )

    # This one fails as it couldn't fetch the new token
    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(
            return_value=(
                True,
                Mock(json=lambda: {"access_token": "xxx", "expires_in": 1234}),
            )
        ),
    ):
        integration.new_hire = new_hire
        integration.renew_key()

        integration.refresh_from_db()
        assert integration.extra_args["oauth"] == {
            "access_token": "xxx",
            "expires_in": 1234,
        }
        # Only one because of previous request
        assert (
            Notification.objects.filter(notification_type="failed_integration").count()
            == 1
        )


@pytest.mark.django_db
def test_integration_send_email(
    client, django_user_model, new_hire_factory, mailoutbox, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={
            "oauth": {},
            "initial_data_form": [{"id": "PASSWORD", "name": "generate"}],
            "execute": [],
            "post_execute_notification": [
                {
                    "type": "email",
                    "subject": "Welcome {{first_name}}",
                    "message": "Here is your password: {{PASSWORD}}",
                    "to": "{{email}}",
                }
            ],
        },
        expiring=timezone.now() - timedelta(days=1),
    )
    new_hire = new_hire_factory()
    integration.execute(new_hire, {})

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == f"Welcome {new_hire.first_name}"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == new_hire.email
    assert "Here is your password:" in mailoutbox[0].body
    assert "{{PASSWORD}}" not in mailoutbox[0].body


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
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"access_token": "test"}))),
)
def test_integration_clean_error_data(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        extra_args={
            "SECRET_KEY": "123",
        }
    )
    assert (
        integration.clean_response("test 123 error")
        == "test ***Secret value for SECRET_KEY*** error"
    )


@pytest.mark.django_db
# Returns text instead of request object
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(False, '{"details": "failed_auth"}')),
)
def test_integration_oauth_callback_failed_view(
    client, django_user_model, custom_integration_factory
):
    client.force_login(django_user_model.objects.create(role=1))
    integration = custom_integration_factory(
        manifest={
            "oauth": {
                "access_token": {"url": "http://localhost:8000/test/?key=123"},
                "authenticate_url": "http://localhost:8000/test/",
            }
        }
    )

    url = reverse("integrations:oauth-callback", args=[integration.id])
    response = client.get(url + "?code=test", follow=True)

    integration.refresh_from_db()
    assert not integration.enabled_oauth
    assert integration.extra_args == {}
    assert (
        "Couldn&#x27;t save token: {&quot;details&quot;: &quot;failed_auth&quot;}"
        in response.content.decode()
    )


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
