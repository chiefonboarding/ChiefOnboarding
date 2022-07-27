import pytest
from django.core.management import call_command
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


@pytest.fixture
def setup_rest_db(settings, django_db_blocker, admin_factory):
    settings.API_ACCESS = True

    admin = admin_factory()
    with django_db_blocker.unblock():
        call_command("migrate", "--noinput")

    Token.objects.create(user=admin, key="testtoken")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token testtoken")

    return client


@pytest.mark.django_db
def test_employees_endpoint(setup_rest_db, new_hire_factory):
    new_hire = new_hire_factory()

    client = setup_rest_db

    request = client.get(reverse("api:employees"), format="json")
    assert request.json()[1] == {
        "id": new_hire.id,
        "first_name": new_hire.first_name,
        "last_name": new_hire.last_name,
        "email": new_hire.email,
    }


@pytest.mark.django_db
def test_sequences_endpoint(setup_rest_db, sequence_factory):

    client = setup_rest_db

    seq1 = sequence_factory()
    seq2 = sequence_factory()

    request = client.get(reverse("api:sequences"), format="json")
    assert request.json() == [
        {"id": seq1.id, "name": seq1.name},
        {"id": seq2.id, "name": seq2.name},
    ]
