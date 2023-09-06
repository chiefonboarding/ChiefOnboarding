import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from admin.introductions.models import Introduction
from users.factories import *  # noqa

from .factories import *  # noqa


@pytest.mark.django_db
def test_create_introduction(client, django_user_model, employee_factory):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    employee = employee_factory()

    url = reverse("introductions:create")
    response = client.get(url)

    assert "Create introduction item" in response.content.decode()

    data = {
        "name": "Intro item 1",
        "tags": ["hi", "whoop"],
    }

    # try posting without into person
    response = client.post(url, data, follow=True)

    assert response.status_code == 200
    # Can't do it, because we have to enter employee
    assert "field is required" in response.content.decode()

    # Test preview view
    url = reverse("introductions:preview", args=[employee.id])
    response = client.get(url)

    assert employee.first_name in response.content.decode()
    assert employee.last_name in response.content.decode()
    assert employee.message in response.content.decode()

    url = reverse("introductions:create")
    data["intro_person"] = employee.id
    response = client.post(url, data, follow=True)

    assert Introduction.objects.all().count() == 1


@pytest.mark.django_db
def test_update_introduction(
    client, django_user_model, employee_factory, introduction_factory
):
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )
    introduction = introduction_factory()
    initial_selected_colleague = introduction.intro_person
    employee = employee_factory()

    url = reverse("introductions:update", args=[introduction.id])
    response = client.get(url)

    # Test if current employee is showing up in preview
    assert (
        '<h3 class="m-0 mb-1">' + initial_selected_colleague.full_name + "</h3>"
        in response.content.decode()
    )

    # Update to other employee
    data = {
        "id": 1,
        "name": "Intro item 1",
        "tags": ["hi", "whoop"],
        "intro_person": employee.id,
    }
    response = client.post(introduction.update_url, data, follow=True)

    # Get intro item again
    url = reverse("introductions:update", args=[introduction.id])
    response = client.get(url)

    assert (
        '<h3 class="m-0 mb-1">' + initial_selected_colleague.full_name + "</h3>"
        not in response.content.decode()
    )

    # Get updated intro item
    introduction.refresh_from_db()

    assert (
        '<h3 class="m-0 mb-1">' + introduction.intro_person.full_name + "</h3>"
        in response.content.decode()
    )
    assert introduction.intro_person.first_name in response.content.decode()
    assert introduction.intro_person == employee

    assert Introduction.objects.all().count() == 1
