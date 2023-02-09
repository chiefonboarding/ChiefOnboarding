import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from admin.preboarding.factories import *  # noqa
from admin.preboarding.models import Preboarding
from users.factories import *  # noqa


@pytest.mark.django_db
def test_create_preboarding(client, django_user_model):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    url = reverse("preboarding:create")
    response = client.get(url)

    assert "Create preboarding item" in response.content.decode()

    data = {
        "name": "Badge item 1",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Preboarding.objects.all().count() == 1


@pytest.mark.django_db
def test_update_preboarding(client, django_user_model, preboarding_factory):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    preboarding = preboarding_factory()

    url = reverse("preboarding:update", args=[preboarding.id])
    response = client.get(url)

    data = {
        "id": 1,
        "name": "Preboarding item 1",
        "content": '{ "time": 0, "blocks": [] }',
        "tags": ["hi", "whoop"],
    }

    response = client.post(url, data, follow=True)
    assert "Preboarding item 1" in response.content.decode()

    assert response.status_code == 200

    assert Preboarding.objects.all().count() == 1
