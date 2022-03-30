import pytest
from django.urls import reverse

from admin.badges.models import Badge
from users.factories import *  # noqa

from .factories import *  # noqa


@pytest.mark.django_db
def test_create_badge(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("badges:create")
    response = client.get(url)

    assert "Create badge item" in response.content.decode()

    data = {
        "name": "Badge item 1",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Badge.objects.all().count() == 1


@pytest.mark.django_db
def test_update_badge(client, django_user_model, badge_factory):
    client.force_login(django_user_model.objects.create(role=1))
    badge = badge_factory()

    url = reverse("badges:update", args=[badge.id])
    response = client.get(url)

    data = {
        "id": 1,
        "name": "Badge item 1",
        "content": '{ "time": 0, "blocks": [] }',
        "tags": ["hi", "whoop"],
    }

    response = client.post(url, data, follow=True)
    assert "Badge item 1" in response.content.decode()

    assert response.status_code == 200

    assert Badge.objects.all().count() == 1
