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

