import pytest

from .models import User


@pytest.mark.django_db
def test_new_hire_create():
    user = User.objects.create_new_hire("john", "smith", "lennon@thebeatles.com", "johnpassword")
    assert user.role == 0
    assert User.objects.count() == 1
