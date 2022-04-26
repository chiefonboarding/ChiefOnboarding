from unittest.mock import Mock, patch
import pytest

from django.urls import reverse


@pytest.fixture
def incomming_message_payload():
    return {
        "token": "xxxxxx",
        "team_id": "T061EG3I6",
        "api_app_id": "A0P343K2",
        "event": {
            "type": "message",
            "channel": "D0243491L",
            "user": "U2147483497",
            "text": "show me to do items",
            "ts": "1355514523.000005",
            "event_ts": "133417523.000005",
            "channel_type": "im"
        },
        "type": "event_callback",
        "authed_teams": [
            "T061349R6"
        ],
        "event_id": "Ev0P342K21",
        "event_time": 13553437523
    }

@pytest.mark.django_db
def test_slack_bot_validate_challenge(
    client, integration_factory
):
    integration_factory(integration=0, token="test")

    url = reverse("slack:bot")

    response = client.post(url, { "token": "test", "challenge": "challenge_output", "type": "url_verification" })

    assert "challenge_output" in response.content.decode()


@pytest.mark.django_db
def test_slack_bot_invalid_token(
    client, integration_factory
):
    integration_factory(integration=0, token="test")

    url = reverse("slack:bot")

    response = client.post(url, { "token": "text", "challenge": "challenge_output", "type": "url_verification" })

    assert "challenge_output" not in response.content.decode()
    assert response.status_code == 200


@pytest.mark.django_db
@patch(
    "slack_bot.utils.Slack.send_message",
    Mock(
        return_value=[
            ["general", False],
            ["introductions", False],
            ["somethingprivate", True],
        ]
    ),
)
def test_slack_bot_user_does_not_exist(
    client, integration_factory, new_hire_factory, incomming_message_payload
):
    integration_factory(integration=0, token="xxxxxx")

    new_hire = new_hire_factory()

    url = reverse("slack:bot")

    response = client.post(url, incomming_message_payload)

    response

