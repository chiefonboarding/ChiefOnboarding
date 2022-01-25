import pytest
from django.urls import reverse

from users.factories import *
from users.models import User


@pytest.mark.django_db
@pytest.mark.parametrize(
    "email, password, status_code",
    [
        ("", "", 400),
        ("", "strong_pass", 400),
        ("user@example.com", "", 400),
        ("user@example.com", "invalid_pass", 400),
        ("user@example.com", "strong_pass", 200),
    ],
)
def test_login_data_validation(email, password, status_code, client, new_hire_factory):
    new_hire = new_hire_factory(email="user@example.com")
    new_hire.set_password("strong_pass")
    new_hire.save()

    url = reverse("login-url")
    data = {"username": email, "password": password}
    response = client.post(url, data=data)
    assert response.status_code == status_code
