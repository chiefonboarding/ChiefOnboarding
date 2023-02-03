from freezegun.api import freeze_time
import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def setup_rest(admin_factory):
    admin = admin_factory()
    Token.objects.create(user=admin, key="testtoken")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token testtoken")

    return client


@pytest.mark.django_db
def test_wrong_token_request(setup_rest):
    client = APIClient()
    # wrong token
    client.credentials(HTTP_AUTHORIZATION="Token testtoken1")

    response = client.get(reverse("api:employees"), format="json")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token."}

    # No token at all
    client = APIClient()
    response = client.get(reverse("api:employees"), format="json")
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication credentials were not provided."
    }


@pytest.mark.django_db
def test_session_request(client, admin_factory):
    # Only token allowed, so this should fail
    admin = admin_factory()
    client.force_login(admin)

    response = client.get(reverse("api:employees"))
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Authentication credentials were not provided."
    }


@pytest.mark.django_db
@override_settings(API_ACCESS=False)
@pytest.mark.urls("api.urls")
def test_api_disabled():
    client = APIClient()

    response = client.get("/api/employees/", format="json")
    assert response.status_code == 404


@pytest.mark.django_db
def test_only_admin_tokens_are_valid(new_hire_factory):
    new_hire = new_hire_factory()
    Token.objects.create(user=new_hire, key="testtoken")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Token testtoken")

    response = client.get(reverse("api:employees"), format="json")
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }


@pytest.mark.django_db
def test_employees_endpoint(setup_rest, new_hire_factory):
    new_hire = new_hire_factory()

    client = setup_rest

    response = client.get(reverse("api:employees"), format="json")
    # Getting the second one as the first one was created with the token
    assert response.json()[1] == {
        "id": new_hire.id,
        "first_name": new_hire.first_name,
        "last_name": new_hire.last_name,
        "email": new_hire.email,
    }


@pytest.mark.django_db
def test_sequences_endpoint(setup_rest, sequence_factory):

    client = setup_rest

    seq1 = sequence_factory()
    seq2 = sequence_factory()

    response = client.get(reverse("api:sequences"), format="json")
    assert response.json() == [
        {"id": seq1.id, "name": seq1.name},
        {"id": seq2.id, "name": seq2.name},
    ]


@pytest.mark.django_db
def test_create_new_hire_endpoint(setup_rest, sequence_factory):

    client = setup_rest

    seq1 = sequence_factory()

    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "sequences": [seq1.id],
            "role": 0,
        },
        format="json",
    )
    assert response.status_code == 201
    # We already have the user with the token + this new hire
    assert User.objects.count() == 2
    assert User.objects.filter(role=0).count() == 1


@pytest.mark.django_db
def test_create_new_hire_with_invalid_options(setup_rest, sequence_factory):

    client = setup_rest

    seq1 = sequence_factory()

    # Buddy does not exist
    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "sequences": [seq1.id],
            "buddy": 1999999,
            "role": 0,
        },
        format="json",
    )
    assert response.status_code == 400
    assert User.objects.count() == 1

    assert response.json() == {
        "buddy": ['Invalid pk "1999999" - object does not exist.']
    }

    # Timezone does not exist
    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "sequences": [seq1.id],
            "timezone": "falsetimezone",
            "role": 0,
        },
        format="json",
    )
    assert response.status_code == 400
    assert User.objects.count() == 1

    assert response.json() == {"timezone": ['"falsetimezone" is not a valid choice.']}

    # Sequence does not exist
    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "sequences": [2412343434],
            "role": 0,
        },
        format="json",
    )
    assert response.status_code == 400
    assert User.objects.count() == 1

    # Role was not provided
    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "sequences": [2412343434],
            "role": 0,
        },
        format="json",
    )
    assert response.status_code == 400
    assert User.objects.count() == 1

    assert response.json() == {"sequences": ["Not all sequence ids are valid."]}


@pytest.mark.django_db
@freeze_time("2022-05-13 08:00:00")
def test_create_new_hire_with_buddy_and_manager(setup_rest, admin_factory, mailoutbox):

    client = setup_rest

    admin1 = admin_factory()
    admin2 = admin_factory()
    # No emails
    assert len(mailoutbox) == 0

    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "buddy": admin1.id,
            "manager": admin2.id,
            "role": 0,
        },
        format="json",
    )
    assert len(mailoutbox) == 1
    assert "Welcome to" in mailoutbox[0].subject
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == "john@chiefonboarding.com"

    assert response.status_code == 201
    assert User.objects.count() == 4

    new_hire = User.objects.last()
    assert new_hire.buddy == admin1


@pytest.mark.django_db
def test_create_admin_user(setup_rest, mailoutbox):

    client = setup_rest

    # No emails
    assert len(mailoutbox) == 0

    response = client.post(
        reverse("api:users"),
        data={
            "first_name": "john",
            "last_name": "Do",
            "email": "john@chiefonboarding.com",
            "role": 1,
        },
        format="json",
    )
    assert len(mailoutbox) == 1
    assert "Your login credentials" in mailoutbox[0].subject
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == "john@chiefonboarding.com"

    assert response.status_code == 201
    assert User.objects.count() == 2

    user = User.objects.last()
    assert user.is_admin
