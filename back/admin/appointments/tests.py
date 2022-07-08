import pytest
from django.urls import reverse

from admin.appointments.models import Appointment


@pytest.mark.django_db
def test_create_appointment(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("appointments:create")
    response = client.get(url)

    assert "Create appointment item" in response.content.decode()

    data = {
        "name": "Appointment item 1",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
        "on_day": 3,
    }

    response = client.post(url, data, follow=True)

    assert response.status_code == 200

    assert Appointment.objects.all().count() == 1

    data = {
        "name": "Appointment item 2",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
        "fixed_date": ["on"],
        "on_day": 3,
    }

    # Will fail because we are missing two values (date and time)
    response = client.post(url, data, follow=True)
    # Did not create a new one
    assert Appointment.objects.all().count() == 1
    assert "This field is required" in response.content.decode()

    data["time"] = "12:14:00"

    # Will fail because date is still missing
    response = client.post(url, data, follow=True)
    # Did not create a new one
    assert Appointment.objects.all().count() == 1
    assert "This field is required" in response.content.decode()

    data["date"] = "2021-12-01"

    # Will succeed
    response = client.post(url, data, follow=True)

    # Created new item
    assert Appointment.objects.all().count() == 2


@pytest.mark.django_db
def test_create_appointment_without_fixed_date(client, django_user_model):
    client.force_login(django_user_model.objects.create(role=1))

    url = reverse("appointments:create")
    response = client.get(url)

    data = {
        "name": "Appointment item 1",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
    }

    response = client.post(url, data, follow=True)

    assert "This field is required." == response.context["form"].errors["on_day"][0]
    assert Appointment.objects.all().count() == 0

    data["on_day"] = 2

    response = client.post(url, data, follow=True)
    assert Appointment.objects.all().count() == 1

    assert response.status_code == 200


@pytest.mark.django_db
def test_update_appointment(client, django_user_model, appointment_factory):
    client.force_login(django_user_model.objects.create(role=1))
    appointment = appointment_factory()

    url = reverse("appointments:update", args=[appointment.id])
    response = client.get(url)

    data = {
        "id": 1,
        "name": "Appointment item 1",
        "tags": ["hi", "whoop"],
        "content": '{ "time": 0, "blocks": [] }',
        "on_day": 3,
    }

    response = client.post(url, data, follow=True)
    assert "Appointment item 1" in response.content.decode()

    assert response.status_code == 200

    assert Appointment.objects.all().count() == 1
