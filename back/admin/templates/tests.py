import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import reverse

from admin.appointments.factories import AppointmentFactory  # noqa
from admin.badges.factories import BadgeFactory  # noqa
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
    ],
)
def test_templates_crud(
    client,
    django_user_model,
    url,
    app,
    model,
):
    # Force admin to login
    client.force_login(
        django_user_model.objects.create(role=get_user_model().Role.ADMIN)
    )

    # Get list view of template
    url = reverse(url)
    response = client.get(url)

    # There aren't any objects yet
    assert "No items available" in response.content.decode()

    # Create template object for every template and 2 non-template
    ToDoFactory()
    ToDoFactory(template=False)
    ToDoFactory(template=False)

    IntroductionFactory()
    IntroductionFactory(template=False)
    IntroductionFactory(template=False)

    BadgeFactory()
    BadgeFactory(template=False)
    BadgeFactory(template=False)

    PreboardingFactory()
    PreboardingFactory(template=False)
    PreboardingFactory(template=False)

    AppointmentFactory()
    AppointmentFactory(template=False)
    AppointmentFactory(template=False)

    ResourceFactory()
    ResourceFactory(template=False)
    ResourceFactory(template=False)

    # Get first object of template
    object_model = apps.get_model(app, model)
    obj = object_model.objects.first()

    # Check list page again
    response = client.get(url)

    # Should be one object
    assert "No items available" not in response.content.decode()
    assert obj.name in response.content.decode()

    # Go to object
    response = client.get(obj.update_url)
    assert response.status_code == 200
    assert obj.name in response.content.decode()

    url = reverse("templates:duplicate", args=[model, obj.id])
    response = client.post(url)

    assert object_model.objects.all().count() == 4
    assert object_model.templates.all().count() == 2

    # Delete first object
    response = client.post(obj.delete_url, follow=True)
    assert response.status_code == 200
    # Second object is still here
    assert "(duplicate)" in response.content.decode()
    assert object_model.templates.all().count() == 1
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
