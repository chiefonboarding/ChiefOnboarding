import base64
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django_q.models import Schedule

from admin.integrations.sync_userinfo import SyncUsers
from admin.integrations.utils import get_value_from_notation
from admin.integrations.models import Integration
from organization.models import Notification


@pytest.mark.django_db
def test_create_integration(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("integrations:create")
    response = client.get(url)

    assert "Add new integration" in response.content.decode()

    # Post with invalid JSON
    response = client.post(url, {"name": "test", "manifest": '{"test": "Test",}'})

    assert "Enter a valid JSON." in response.content.decode()

    # Post with valid JSON
    response = client.post(
        url,
        {
            "name": "test",
            "manifest": '{"form": [],"execute": []}',
            "manifest_type": Integration.ManifestType.WEBHOOK,
        },
    )

    assert "Enter a valid JSON." not in response.content.decode()
    assert Integration.objects.filter(integration=Integration.Type.CUSTOM).count() == 1


@pytest.mark.django_db
def test_create_sync_integration(client, django_user_model):
    create_url = reverse("integrations:create")

    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    client.post(
        create_url,
        {
            "name": "test",
            "manifest": '{"action": "create","execute": [],"data_structure": {"first_name": "first_name" }}',  # noqa
            "manifest_type": Integration.ManifestType.SYNC_USERS,
        },
    )

    integration = Integration.objects.first()

    update_url = reverse("integrations:update", args=[integration.id])

    assert (
        Integration.objects.filter(
            manifest_type=Integration.ManifestType.SYNC_USERS
        ).count()
        == 1
    )
    schedule = Schedule.objects.filter(
        name=f"User sync for integration: {integration.id}"
    ).first()

    # schedule is not there, since there was no schedule provided
    assert schedule is None

    # add schedule
    client.post(
        update_url,
        {
            "name": "test",
            "manifest": '{"action": "create","execute": [],"data_structure": {"first_name": "first_name" }, "schedule": "* * * * *"}',  # noqa
            "manifest_type": Integration.ManifestType.SYNC_USERS,
        },
    )

    schedule = Schedule.objects.filter(
        name=f"User sync for integration: {integration.id}"
    ).first()
    assert schedule is not None
    assert schedule.cron == "* * * * *"

    # update to change cron
    client.post(
        update_url,
        {
            "name": "test",
            "manifest": '{"action": "create","execute": [],"data_structure": {"first_name": "first_name" }, "schedule": "* 1 * * *"}',  # noqa
            "manifest_type": Integration.ManifestType.SYNC_USERS,
        },
    )

    schedule.refresh_from_db()
    assert schedule is not None
    assert schedule.cron == "* 1 * * *"

    # delete to test if schedule is gone
    url = reverse("integrations:delete", args=[integration.id])
    client.post(url, follow=True)

    assert not Schedule.objects.filter(
        name=f"User sync for integration: {integration.id}"
    ).exists()


@pytest.mark.django_db
def test_update_integration(client, django_user_model, custom_integration_factory):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    integration = custom_integration_factory()

    url = reverse("integrations:update", args=[integration.id])
    response = client.get(url)

    assert "Update existing integration" in response.content.decode()
    assert "TEAM_ID" in response.content.decode()
    assert integration.name in response.content.decode()


@pytest.mark.django_db
def test_create_google_login_integration(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("integrations:create-google")
    response = client.get(url)

    assert "client_id" in response.content.decode()
    assert "client_secret" in response.content.decode()

    response = client.post(url, data={"client_id": "12", "client_secret": "233"})

    assert (
        Integration.objects.filter(integration=Integration.Type.GOOGLE_LOGIN).count()
        == 1
    )


@pytest.mark.django_db
def test_delete_integration(client, django_user_model, custom_integration_factory):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    integration = custom_integration_factory()

    assert Integration.objects.filter(integration=Integration.Type.CUSTOM).count() == 1

    url = reverse("integrations:delete", args=[integration.id])
    response = client.get(url, follow=True)

    assert (
        "Are you sure you want to remove this integration?" in response.content.decode()
    )

    response = client.delete(url, follow=True)

    assert reverse("settings:integrations") in response.redirect_chain[-1][0]
    assert Integration.objects.filter(integration=Integration.Type.CUSTOM).count() == 0


@pytest.mark.django_db
def test_integration_extra_args_form(
    client, django_user_model, custom_integration_factory
):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
        integration.has_user_context = True
        integration.renew_key()

        assert (
            Notification.objects.filter(
                notification_type=Notification.Type.FAILED_INTEGRATION
            ).count()
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
            Notification.objects.filter(
                notification_type=Notification.Type.FAILED_INTEGRATION
            ).count()
            == 1
        )


@pytest.mark.django_db
def test_integration_send_email(
    client, django_user_model, new_hire_factory, mailoutbox, custom_integration_factory
):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
def test_integration_clean_error_data(custom_integration_factory):
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
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
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    # Google login is disabled, so url doesn't work
    url = reverse("integrations:slack")
    response = client.get(url, follow=True)

    # No code available
    assert response.status_code == 200
    assert "Could not optain slack authentication code." in response.content.decode()

    response = client.get(url + "?code=test", follow=True)

    assert response.status_code == 200

    assert Integration.objects.filter(integration=Integration.Type.SLACK_BOT).exists()
    assert "Slack has successfully been connected." in response.content.decode()


@pytest.mark.django_db
def test_get_value_from_notation():
    # test deep lookup through dictionaries
    test_data = {"one": {"0": {"deep": "yes"}}}

    # the 0 gets used as a prop
    result = get_value_from_notation("one.0.deep", test_data)
    assert result == "yes"

    # test lookup with array inbetween
    test_data = {"one": [{"deep": "yes"}]}

    # the 0 gets used as the index for the array
    result = get_value_from_notation("one.0.deep", test_data)
    assert result == "yes"

    # test invalid lookup with array inbetween
    test_data = {"one": [{"deep": "yes"}]}

    # the 1 gets used as the index for the array, but we don't have it, so raise error
    with pytest.raises(KeyError):
        get_value_from_notation("one.1.deep", test_data)

    # test normal invalid lookup
    test_data = {"one": "yes"}
    with pytest.raises(KeyError):
        get_value_from_notation("two", test_data)


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"user_data": {"user_id": 123}}))),
)
def test_integration_save_data_to_user(new_hire_factory, custom_integration_factory):
    new_hire = new_hire_factory()

    assert new_hire.extra_fields == {}

    integration = custom_integration_factory(
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                    "store_data": {"FORM_ID": "user_data.user_id"},
                }
            ]
        }
    )

    integration.execute(new_hire, {})

    new_hire.refresh_from_db()

    assert new_hire.extra_fields == {"FORM_ID": 123}


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"user": {"user_id": 123}}))),
)
def test_integration_save_data_to_user_invalid_lookup(
    new_hire_factory, custom_integration_factory
):
    new_hire = new_hire_factory()

    assert new_hire.extra_fields == {}

    integration = custom_integration_factory(
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                    "store_data": {"FORM_ID": "user_data.user_id"},
                }
            ]
        }
    )

    result = integration.execute(new_hire, {})

    assert result == (
        False,
        "Could not store data to new hire: "
        "user_data.user_id not found in {'user': {'user_id': 123}}",
    )

    new_hire.refresh_from_db()

    assert new_hire.extra_fields == {}


@pytest.mark.django_db
def test_polling_not_getting_correct_state(
    monkeypatch, new_hire_factory, custom_integration_factory
):
    new_hire = new_hire_factory()

    integration = custom_integration_factory(
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                    "polling": {
                        # very small number to not let task hang too long
                        "interval": 0.1,
                        "amount": 3,
                    },
                    "continue_if": {
                        "response_notation": "status",
                        "value": "done",
                    },
                }
            ]
        }
    )

    with patch(
        "admin.integrations.models.Integration.run_request",
        Mock(
            side_effect=(
                # first call
                [
                    True,
                    Mock(json=lambda: {"status": "not_done"}),
                ],
                # second call
                [
                    True,
                    Mock(json=lambda: {"status": "not_done"}),
                ],
                # third call
                [
                    True,
                    Mock(json=lambda: {"status": "not_done"}),
                ],
                # fourth call (will never reach this)
                [
                    True,
                    Mock(json=lambda: {"status": "done"}),
                ],
            )
        ),
    ) as request_mock:
        success, _response = integration.execute(new_hire, {})

    assert request_mock.call_count == 3
    assert success is False


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        side_effect=(
            # first call
            [
                True,
                Mock(json=lambda: {"status": "not_done"}),
            ],
            # second call
            [
                True,
                Mock(json=lambda: {"status": "done"}),
            ],
        )
    ),
)
def test_polling_getting_correct_state(new_hire_factory, custom_integration_factory):
    new_hire = new_hire_factory()

    integration = custom_integration_factory(
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                    "polling": {
                        # very small number to not let task hang too long
                        "interval": 0.1,
                        "amount": 3,
                    },
                    "continue_if": {
                        "response_notation": "status",
                        "value": "done",
                    },
                }
            ]
        }
    )

    success, _response = integration.execute(new_hire, {})

    assert success is True


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"status": "not_done"}))),
)
def test_block_integration_on_condition(new_hire_factory, custom_integration_factory):
    new_hire = new_hire_factory()

    integration = custom_integration_factory(
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                    "continue_if": {
                        "response_notation": "status",
                        "value": "done",
                    },
                }
            ]
        }
    )

    success, _response = integration.execute(new_hire, {})

    assert success is False


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(return_value=(True, Mock(json=lambda: {"details": "DOSOMETHING#"}))),
)
def test_integration_reuse_data_from_previous_request(
    client, django_user_model, new_hire_factory, custom_integration_factory
):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    integration = custom_integration_factory(
        manifest={
            "execute": [{"url": "http://localhost/", "method": "POST"}],
        },
    )
    new_hire = new_hire_factory()
    integration.execute(new_hire, {})
    assert integration.params["responses"] == [{"details": "DOSOMETHING#"}]

    assert (
        integration._replace_vars("test {{responses.0.details}}") == "test DOSOMETHING#"
    )


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        return_value=(
            True,
            Mock(
                json=lambda: [
                    {"email": "test1@chiefonboarding.com", "external_id": 123},
                    {"email": "test2@chiefonboarding.com", "external_id": 344},
                    {"email": "test3@chiefonboarding.com", "external_id": 334},
                    {"email": "test4@chiefonboarding.com", "external_id": 335},
                    {"email": "test5@chiefonboarding.com"},
                ]
            ),
        )
    ),
)
def test_integration_sync_data(new_hire_factory, custom_integration_factory):
    new_hire1 = new_hire_factory(email="test1@chiefonboarding.com")
    new_hire2 = new_hire_factory(email="test2@chiefonboarding.com")
    new_hire3 = new_hire_factory(email="test5@chiefonboarding.com")
    new_hire4 = new_hire_factory(email="test6@chiefonboarding.com")

    assert new_hire1.extra_fields == {}
    assert new_hire2.extra_fields == {}
    assert new_hire3.extra_fields == {}
    assert new_hire4.extra_fields == {}

    integration = custom_integration_factory(
        manifest_type=Integration.ManifestType.SYNC_USERS,
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                }
            ],
            "data_from": "",
            "action": "update",
            "data_structure": {"email": "email", "EXT_ID": "external_id"},
        },
    )

    SyncUsers(integration).run()

    new_hire1.refresh_from_db()
    assert new_hire1.extra_fields == {"EXT_ID": 123}

    new_hire2.refresh_from_db()
    assert new_hire2.extra_fields == {"EXT_ID": 344}

    # no `external_id` data, so blank
    new_hire3.refresh_from_db()
    assert new_hire3.extra_fields == {}

    # not in dataset from the API
    new_hire4.refresh_from_db()
    assert new_hire4.extra_fields == {}


@pytest.mark.django_db
@patch(
    "admin.integrations.models.Integration.run_request",
    Mock(
        return_value=(
            True,
            Mock(
                json=lambda: [
                    {
                        "email": "test1@chiefonboarding.com",
                        "firstName": "test1",
                        "lastName": "1",
                    },
                    {
                        "email": "test2@chiefonboarding.com",
                        "firstName": "test2",
                        "lastName": "2",
                    },
                    {
                        "email": "test3@chiefonboarding.com",
                        "firstName": "test3",
                        "lastName": "3",
                    },
                    {
                        "email": "test4@chiefonboarding.com",
                        "firstName": "test4",
                        "lastName": "4",
                    },
                    {"email": "test5@chiefonboarding.com"},
                ]
            ),
        )
    ),
)
def test_integration_sync_data_create_users(
    new_hire_factory, custom_integration_factory
):
    new_hire1 = new_hire_factory(email="test1@chiefonboarding.com")

    assert new_hire1.extra_fields == {}

    integration = custom_integration_factory(
        manifest_type=Integration.ManifestType.SYNC_USERS,
        manifest={
            "execute": [
                {
                    "url": "http://localhost/",
                }
            ],
            "data_from": "",
            "action": "create",
            "data_structure": {
                "first_name": "firstName",
                "last_name": "lastName",
                "email": "email",
            },
        },
    )

    SyncUsers(integration).run()

    new_hire1.refresh_from_db()
    # didn't do anything with newhire1 as it only creates users
    assert new_hire1.extra_fields == {}

    assert get_user_model().objects.all().count() == 4
    # randomly checking users to make sure their data is correct
    assert get_user_model().objects.filter(email="test2@chiefonboarding.com").exists()
    assert (
        get_user_model().objects.get(email="test3@chiefonboarding.com").first_name
        == "test3"
    )
    assert (
        get_user_model().objects.get(email="test4@chiefonboarding.com").last_name == "4"
    )
    assert (
        not get_user_model().objects.filter(email="test5@chiefonboarding.com").exists()
    )
