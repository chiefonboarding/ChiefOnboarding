import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse

from users.factories import DepartmentFactory
from admin.appointments.factories import AppointmentFactory  # noqa
from admin.badges.factories import BadgeFactory  # noqa
from admin.hardware.factories import HardwareFactory  # noqa
from admin.introductions.factories import IntroductionFactory  # noqa
from admin.preboarding.factories import PreboardingFactory  # noqa
from admin.resources.factories import ResourceFactory  # noqa
from admin.sequences.models import Sequence  # noqa
from admin.to_do.factories import ToDoFactory  # noqa


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url, app, model",
    [
        ("todo:list", "to_do", "todo"),
        ("introductions:list", "introductions", "introduction"),
        ("badges:list", "badges", "badge"),
        ("preboarding:list", "preboarding", "preboarding"),
        ("appointments:list", "appointments", "appointment"),
        ("resources:list", "resources", "resource"),
        ("hardware:list", "hardware", "hardware"),
    ],
)
def test_templates_crud(
    client,
    django_user_model,
    url,
    app,
    model,
):
    # Force manager to login
    dep = DepartmentFactory()
    not_part_of_dep = DepartmentFactory()
    manager = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    # has one department
    manager.departments.set([dep])

    client.force_login(manager)

    # Get list view of template
    url = reverse(url)
    response = client.get(url)

    # There aren't any objects yet
    assert "No items available" in response.content.decode()

    # Create template object for every template and 2 non-template
    ToDoFactory()
    ToDoFactory(departments=[dep])
    ToDoFactory(departments=[not_part_of_dep])
    ToDoFactory(template=False)
    ToDoFactory(template=False)

    IntroductionFactory()
    IntroductionFactory(departments=[dep])
    IntroductionFactory(departments=[not_part_of_dep])
    IntroductionFactory(template=False)
    IntroductionFactory(template=False)

    BadgeFactory()
    BadgeFactory(departments=[dep])
    BadgeFactory(departments=[not_part_of_dep])
    BadgeFactory(template=False)
    BadgeFactory(template=False)

    PreboardingFactory()
    PreboardingFactory(departments=[dep])
    PreboardingFactory(departments=[not_part_of_dep])
    PreboardingFactory(template=False)
    PreboardingFactory(template=False)

    AppointmentFactory()
    AppointmentFactory(departments=[dep])
    AppointmentFactory(departments=[not_part_of_dep])
    AppointmentFactory(template=False)
    AppointmentFactory(template=False)

    ResourceFactory()
    ResourceFactory(departments=[dep])
    ResourceFactory(departments=[not_part_of_dep])
    ResourceFactory(template=False)
    ResourceFactory(template=False)

    HardwareFactory()
    HardwareFactory(departments=[dep])
    HardwareFactory(departments=[not_part_of_dep])
    HardwareFactory(template=False)
    HardwareFactory(template=False)

    # Get first object of template
    object_model = apps.get_model(app, model)
    obj = object_model.templates.for_user(user=manager).first()
    hidden_obj = object_model.templates.get(departments=not_part_of_dep)

    # Check list page again
    response = client.get(url)

    # Should be one object
    assert "No items available" not in response.content.decode()
    assert obj.name in response.content.decode()
    # The one not in the department should not show
    assert hidden_obj.name not in response.content.decode()

    # Go to object
    response = client.get(obj.update_url)
    assert response.status_code == 200
    assert obj.name in response.content.decode()

    url = reverse("templates:duplicate", args=[model, obj.id])
    response = client.post(url)

    assert object_model.objects.all().count() == 6
    assert object_model.templates.all().count() == 4
    assert object_model.templates.for_user(user=manager).count() == 3

    # Delete first object
    response = client.post(obj.delete_url, follow=True)
    assert response.status_code == 200
    # Second object is still here
    assert "(duplicate)" in response.content.decode()
    assert object_model.templates.all().count() == 3
    assert object_model.templates.for_user(user=manager).count() == 2
    assert "item has been removed" in response.content.decode()


@pytest.mark.django_db
def test_sequence_duplicate(
    client, django_user_model, sequence_factory, condition_with_items_factory
):
    # Force admin to login
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    # Get list view of template
    url = reverse("sequences:list")
    response = client.get(url)
    assert "No items available" in response.content.decode()

    seq = sequence_factory()
    condition_with_items_factory(sequence=seq)

    url = reverse("sequences:list")
    response = client.get(url)
    assert "No items available" not in response.content.decode()

    url = reverse("templates:duplicate_seq", args=[seq.id])
    response = client.post(url)

    assert Sequence.objects.all().count() == 2


@pytest.mark.django_db
def test_departments_mixin_cannot_remove_unassigned_dep(
    client,
    django_user_model,
):
    # Force manager to login
    dep = DepartmentFactory()
    not_part_of_dep = DepartmentFactory()
    manager = django_user_model.objects.create(role=get_user_model().Role.MANAGER)
    # has one department
    manager.departments.set([dep])

    client.force_login(manager)

    to_do = ToDoFactory(departments=[dep, not_part_of_dep])

    data = {
        "name": "to do",
        "content": '{ "time": "0", "blocks": [{ "type": "paragraph" }] }',
        "tags": [],
        "departments": [],
        "due_on_day": 1,
    }
    response = client.post(to_do.update_url, data, follow=True)
    assert "You cannot remove a department that you are not part of" in response.content.decode()

    # only other dep passes
    data["departments"] = [not_part_of_dep.id]
    response = client.post(to_do.update_url, data, follow=True)
    assert "You cannot remove a department that you are not part of" not in response.content.decode()

    # admin can remove any departments
    response = client.post(to_do.update_url, data, follow=True)

    admin = django_user_model.objects.create(role=get_user_model().Role.ADMIN, email="test@example.com")
    client.force_login(admin)

    data["departments"] = [not_part_of_dep.id]
    response = client.post(to_do.update_url, data, follow=True)
    assert "You cannot remove a department that you are not part of" not in response.content.decode()
