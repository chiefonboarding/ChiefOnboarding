import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from admin.admin_tasks.models import AdminTask
from admin.hardware.models import Hardware
from organization.models import Notification


@pytest.mark.django_db
def test_create_hardware_with_assigned_user(client, django_user_model):
    admin_user = django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    client.force_login(admin_user)

    url = reverse("hardware:create")

    # missing assigned user, but selected "custom"
    data = {
        "name": "test",
        "tags": ["test", "test"],
        "content": '{ "time": 0, "blocks": [] }',
        "person_type": 3,
    }

    response = client.post(url, data, follow=True)
    print(response.content.decode())

    assert "This field is required" in response.content.decode()
    assert Hardware.objects.all().count() == 0

    data["assigned_to"] = admin_user.id

    response = client.post(url, data, follow=True)
    assert Hardware.objects.all().count() == 1
    assert response.status_code == 200


@pytest.mark.django_db
def test_hardware_execute(
    employee_factory,
    admin_factory,
    hardware_factory,
):
    emp1 = employee_factory()

    assert emp1.hardware.count() == 0

    # hardware without any notifications
    hardware = hardware_factory()
    hardware.execute(emp1)

    assert emp1.hardware.count() == 1
    assert not AdminTask.objects.all().exists()
    assert Notification.objects.count() == 1

    # run once again for offboarding
    hardware.execute(emp1)
    assert Notification.objects.count() == 2
    assert emp1.hardware.count() == 0

    # create admin task based on manager
    admin1 = admin_factory()
    emp2 = employee_factory(manager=admin1)
    hardware.person_type = Hardware.PersonType.MANAGER
    hardware.save()

    hardware.execute(emp2)
    assert AdminTask.objects.filter(
        new_hire=emp2, assigned_to=admin1, hardware=hardware
    ).exists()
    # not attached to user yet
    assert emp1.hardware.count() == 0
    assert Notification.objects.count() == 3

    # create admin task based on buddy
    admin2 = admin_factory()
    emp3 = employee_factory(buddy=admin2)
    hardware.person_type = Hardware.PersonType.BUDDY
    hardware.save()

    hardware.execute(emp3)
    assert AdminTask.objects.filter(
        new_hire=emp3, assigned_to=admin2, hardware=hardware
    ).exists()

    # create admin task based on specific person
    admin3 = admin_factory()
    emp4 = employee_factory()
    hardware.person_type = Hardware.PersonType.CUSTOM
    hardware.assigned_to = admin3
    hardware.save()

    hardware.execute(emp4)
    assert AdminTask.objects.filter(
        new_hire=emp4, assigned_to=admin3, hardware=hardware
    ).exists()


@pytest.mark.django_db
def test_hardware_admin_task(
    employee_factory,
    admin_factory,
    hardware_factory,
):
    emp1 = employee_factory()
    admin1 = admin_factory()
    hardware = hardware_factory(
        person_type=Hardware.PersonType.CUSTOM, assigned_to=admin1
    )
    hardware.execute(emp1)

    admin_task = AdminTask.objects.get(
        new_hire=emp1, assigned_to=admin1, hardware=hardware
    )
    assert emp1.hardware.count() == 0
    assert Notification.objects.count() == 1

    admin_task.mark_completed()

    assert emp1.hardware.count() == 1
    assert Notification.objects.count() == 2

    # trigger hardware another time for reclaiming hardware
    hardware.execute(emp1)

    # we now have two admin tasks
    assert (
        AdminTask.objects.filter(
            new_hire=emp1, assigned_to=admin1, hardware=hardware
        ).count()
        == 2
    )

    for item in AdminTask.objects.all():
        print(item.name)
    admin_task = AdminTask.objects.get(
        name=f"Reclaim hardware from employee ({emp1.full_name}): {hardware.name}"
    )
    assert not admin_task.completed
    admin_task.mark_completed()

    assert Notification.objects.count() == 4
    assert emp1.hardware.count() == 0
