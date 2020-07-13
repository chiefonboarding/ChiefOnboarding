import pytest
from .models import User, NewHireDetails


@pytest.mark.django_db
def test_new_hire_create():
    user = User.objects.create_new_hire('john', 'smith', 'lennon@thebeatles.com', 'johnpassword')
    assert user.is_admin is False
    assert user.is_manager is False
    assert NewHireDetails.objects.count() == 1
    assert NewHireDetails.objects.all()[0].user.id is user.id
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_manager_create():
    user = User.objects.create_manager('john', 'smith', 'lennon@thebeatles.com', 'johnpassword')
    assert user.is_admin is False
    assert user.is_manager is True
    assert NewHireDetails.objects.count() == 0
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_admin_create():
    user = User.objects.create_admin('john', 'smith', 'lennon@thebeatles.com', 'johnpassword')
    assert user.is_admin is True
    assert user.is_manager is False
    assert NewHireDetails.objects.count() == 0
    assert User.objects.count() == 1
