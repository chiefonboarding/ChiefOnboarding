import pytest
from django.urls import reverse

from admin.to_do.models import ToDo

from .factories import *  # noqa


@pytest.mark.django_db
def test_create_to_do(client, django_user_model, integration_factory):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("todo:create")
    response = client.get(url)

    assert "Create to do item" in response.content.decode()

    data = {
        "name": "new to do",
        "content": '{ "time": "0", "blocks": [{ "type": "paragraph" }] }',
        "tags": ["hi", "whoop"],
        "due_on_day": 1,
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200
    # Check that we are back on the templates page
    assert "To do items" in response.content.decode()

    # Check that item has been created and is in list
    assert "new to do" in response.content.decode()
    assert "hi" in response.content.decode()
    assert "whoop" in response.content.decode()
    assert ToDo.objects.all().count() == 1

    # Should report back to select channel if 'send_back' is enabled

    data = {
        "name": "new to do",
        "send_back": "on",
        "content": '{ "time": "0", "blocks": [{ "type": "paragraph" }] }',
        "tags": ["hi", "whoop"],
        "due_on_day": 1,
    }

    response = client.post(url, data, follow=True)

    # This is disabled, since there is no slack integration
    assert "select a channel" not in response.content.decode()

    # Create the slack bot now
    integration_factory(integration=0)

    response = client.post(url, data, follow=True)

    # This is now an active field
    assert "select a channel" in response.content.decode()

    # not created
    assert ToDo.objects.all().count() == 1

    # Select channel
    data = {
        "name": "new to do",
        "send_back": "on",
        "content": '{ "time": "0", "blocks": [{ "type": "paragraph" }] }',
        "slack_channel": 1,
        "tags": ["hi", "whoop"],
        "due_on_day": 1,
    }

    response = client.post(url, data, follow=True)

    # This should succeed and go back to to do items
    assert "To do items" in response.content.decode()
    # Check if it created one
    assert ToDo.objects.all().count() == 2
