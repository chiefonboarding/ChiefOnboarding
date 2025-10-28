import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.models import Department


@pytest.mark.django_db
def test_department_list(
    client,
    django_user_model,
    department_factory,
    new_hire_factory,
    manager_factory,
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    dep2 = department_factory()
    user.departments.add(dep)

    user1 = new_hire_factory(departments=[dep])
    user2 = new_hire_factory(departments=[dep2])
    user3 = manager_factory(departments=[dep])
    # not part of any departments, so available everywhere
    user4 = manager_factory()

    url = reverse("people:departments")
    response = client.get(url)

    # user1 and user3 are part of their own dep, so they will show up. user4 is not part of an dep, so shows up as well
    assert user1.name in response.content.decode()
    assert user3.name in response.content.decode()
    assert user4.name in response.content.decode()
    # user 2 is part of different dep, so doesn't show up
    assert user2.name not in response.content.decode()

    # dep does not show up
    assert dep2.name not in response.content.decode()


@pytest.mark.django_db
def test_create_new_department(client, django_user_model, department_factory):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    # make other department to make sure it's not showing this
    dep2 = department_factory()

    url = reverse("people:departments")
    response = client.get(url)

    assert "There are no departments yet." in response.content.decode()
    assert dep2.name not in response.content.decode()

    url = reverse("people:department_create")
    response = client.post(url, {"name": "newdepartment"}, follow=True)

    department = Department.objects.get(name="newdepartment")
    # has been added to user
    user.refresh_from_db()
    assert department in user.departments.all()

    assert "Department has been created" in response.content.decode()

    # shows up on list view
    assert "newdepartment" in response.content.decode()
    assert "Add role" in response.content.decode()
    assert "There are no departments yet." not in response.content.decode()


@pytest.mark.django_db
def test_update_department(client, django_user_model, department_factory):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    user.departments.add(dep)

    url = reverse("people:department_update", args=[dep.id])
    response = client.get(url)

    assert "No roles added yet" in response.content.decode()
    assert dep.name in response.content.decode()

    response = client.post(url, {"name": "newdepartment"}, follow=True)

    user.refresh_from_db()
    department = Department.objects.get(name="newdepartment")
    # has been added to user
    assert department in user.departments.all()

    assert "Department has been updated" in response.content.decode()

    # shows up on list view
    assert "newdepartment" in response.content.decode()
    assert "Add role" in response.content.decode()
    assert "There are no departments yet." not in response.content.decode()


@pytest.mark.django_db
def test_update_department_manager_is_not_part_of(
    client, django_user_model, department_factory
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    # 404 when trying to update a department they are not part of
    dep = department_factory()
    url = reverse("people:department_update", args=[dep.id])
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_new_role_in_department(
    client, django_user_model, department_factory, department_role_factory
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    user.departments.add(dep)

    # make other department to make sure it's not showing this
    dep2 = department_factory()
    role1 = department_role_factory(department=dep2)

    url = reverse("people:department_role_create", args=[dep.id])
    response = client.get(url)

    assert "New role" in response.content.decode()

    response = client.post(url, {"name": "newrole"}, follow=True)

    assert "Role has been created" in response.content.decode()

    assert "No users have been added to this role yet." in response.content.decode()
    assert dep2.name not in response.content.decode()
    assert role1.name not in response.content.decode()

    # role shows up when updating department
    url = reverse("people:department_update", args=[dep.id])
    response = client.get(url)

    assert "newrole" in response.content.decode()
    # other role is not showing
    assert role1.name not in response.content.decode()


@pytest.mark.django_db
def test_create_new_role_in_department_manager_is_not_part_of(
    client, django_user_model, department_factory
):
    # make other department to make sure it's not showing this
    dep2 = department_factory()

    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    # 404 when trying to create a role for an org they are not part of
    url = reverse("people:department_role_create", args=[dep2.id])
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_role_in_department(
    client, django_user_model, department_factory, department_role_factory
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    role = department_role_factory(department=dep, name="testrole")
    user.departments.add(dep)

    url = reverse("people:department_role_update", args=[dep.id, role.id])
    response = client.get(url)

    assert "testrole" in response.content.decode()

    response = client.post(url, {"name": "testrole12"}, follow=True)

    assert "Role has been updated" in response.content.decode()

    role.refresh_from_db()
    assert role.name == "testrole12"


@pytest.mark.django_db
def test_update_role_in_other_department(
    client, django_user_model, department_factory, department_role_factory
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    # other role (not owned) gets 404
    dep = department_factory()
    role = department_role_factory(department=dep, name="testrole")

    url = reverse("people:department_role_update", args=[dep.id, role.id])
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_add_user_to_role_in_department(
    client,
    django_user_model,
    department_factory,
    department_role_factory,
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    role = department_role_factory(department=dep, name="testrole")
    user.departments.add(dep)

    # user is not part of role
    assert user not in role.users.all()

    url = reverse("people:add_user_to_role", args=[role.id, user.id])
    client.post(url)

    # user is part of role
    role.refresh_from_db()
    assert user in role.users.all()


@pytest.mark.django_db
def test_department_sequence_list(
    client,
    django_user_model,
    department_factory,
    sequence_factory,
    new_hire_factory,
    manager_factory,
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    dep2 = department_factory()
    user.departments.add(dep)

    seq1 = sequence_factory(departments=[dep])
    seq2 = sequence_factory(departments=[dep2])
    seq3 = sequence_factory(departments=[dep])
    # not part of any departments, so available everywhere
    seq4 = sequence_factory()

    url = reverse("people:departments_sequences")
    response = client.get(url)

    # seq1 and seq2 are part of their own dep, so they will show up. seq4 is not part of an dep, so shows up as well
    assert seq1.name in response.content.decode()
    assert seq3.name in response.content.decode()
    assert seq4.name in response.content.decode()
    # seq2 is part of different dep, so doesn't show up
    assert seq2.name not in response.content.decode()

    # dep does not show up
    assert dep2.name not in response.content.decode()


@pytest.mark.django_db
def test_add_seq_to_role_in_department(
    client,
    django_user_model,
    department_factory,
    department_role_factory,
    sequence_factory,
):
    user = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    client.force_login(user)

    dep = department_factory()
    role = department_role_factory(department=dep, name="testrole")
    seq = sequence_factory(departments=[dep])
    user.departments.add(dep)

    # seq is not part of role
    assert seq not in role.sequences.all()

    url = reverse("people:add_seq_to_role", args=[role.id, seq.id])
    client.post(url)

    # seq is part of role
    role.refresh_from_db()
    assert seq in role.sequences.all()
