import pytest
from django.urls import reverse

from admin.admin_tasks.models import AdminTask


@pytest.mark.django_db
def test_all_tasks_view(client, admin_factory, admin_task_factory):
    admin = admin_factory()
    client.force_login(admin)

    task1 = admin_task_factory(assigned_to=admin)
    task2 = admin_task_factory()

    url = reverse("admin_tasks:all")
    response = client.get(url)

    assert task1.name in response.content.decode()
    assert task2.name in response.content.decode()


@pytest.mark.django_db
def test_my_tasks_view(client, admin_factory, admin_task_factory):
    admin = admin_factory()
    client.force_login(admin)

    task1 = admin_task_factory(assigned_to=admin)
    task2 = admin_task_factory()

    url = reverse("admin_tasks:mine")
    response = client.get(url)

    assert task1.name in response.content.decode()
    assert task2.name not in response.content.decode()


@pytest.mark.django_db
def test_create_admin_task(client, admin_factory, new_hire_factory):
    admin1 = admin_factory()
    new_hire1 = new_hire_factory()
    admin2 = admin_factory(slack_user_id="slack_u_id")
    client.force_login(admin1)

    url = reverse("admin_tasks:create")
    response = client.get(url)

    # Check that the options are there
    assert new_hire1.full_name in response.content.decode()
    assert admin2.full_name in response.content.decode()

    data = {
        "name": "Set up a tour",
        "priority": 1,
        "new_hire": new_hire1.id,
        "assigned_to": admin1.id,
        "comment": "please do this",
        "option": 0,
    }
    response = client.post(url, data=data, follow=True)

    assert "Task has been created" in response.content.decode()
    assert "Set up a tour" in response.content.decode()
    assert AdminTask.objects.all().count() == 1


@pytest.mark.django_db
def test_create_admin_task_for_different_user(
    client, admin_factory, new_hire_factory, mailoutbox
):
    new_hire1 = new_hire_factory()
    admin1 = admin_factory()
    admin2 = admin_factory()
    client.force_login(admin1)

    url = reverse("admin_tasks:create")
    data = {
        "name": "Set up a tour",
        "priority": 1,
        "new_hire": new_hire1.id,
        "assigned_to": admin2.id,
        "comment": "please do this",
        "option": 0,
    }
    client.post(url, data=data, follow=True)

    admin_task = AdminTask.objects.first()

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A task has been assigned to you!"
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == admin2.email
    assert admin_task.name in mailoutbox[0].alternatives[0][0]
    assert admin_task.comment.last().content in mailoutbox[0].alternatives[0][0]


@pytest.mark.django_db
def test_complete_admin_task(client, admin_factory, admin_task_factory):
    admin = admin_factory()
    client.force_login(admin)

    task1 = admin_task_factory(assigned_to=admin)
    task2 = admin_task_factory(assigned_to=admin)

    url = reverse("admin_tasks:mine")
    response = client.get(url)

    assert task1.name in response.content.decode()
    # Checked button is not visible because tasks are still open
    assert "btn-success" not in response.content.decode()

    url = reverse("admin_tasks:detail", args=[task1.id])
    response = client.get(url)

    complete_url = reverse("admin_tasks:completed", args=[task1.id])
    assert "Complete" in response.content.decode()
    assert complete_url in response.content.decode()

    response = client.get(complete_url, follow=True)
    task1.refresh_from_db()
    task2.refresh_from_db()

    assert "Complete" not in response.content.decode()
    assert "completed" in response.content.decode()
    assert "disabled" in response.content.decode()
    # Cannot add new comment
    assert "div_id_content" not in response.content.decode()
    # Complete url is still there to make it open again
    assert complete_url in response.content.decode()

    assert task1.completed
    assert not task2.completed

    url = reverse("admin_tasks:mine")
    response = client.get(url)
    # Check button is now visible
    assert "btn-success" in response.content.decode()


@pytest.mark.django_db
def test_admin_task_post_comment(client, admin_factory, admin_task_factory):
    admin1 = admin_factory()
    admin2 = admin_factory()
    client.force_login(admin1)

    task1 = admin_task_factory(assigned_to=admin1)

    url = reverse("admin_tasks:comment", args=[task1.id])
    response = client.post(url, {"content": "Hi, this is a new comment"}, follow=True)

    url = reverse("admin_tasks:detail", args=[task1.id])
    response = client.get(url)

    assert "Hi, this is a new comment" in response.content.decode()

    # Create a second comment with a new admin user
    client.force_login(admin2)
    url = reverse("admin_tasks:comment", args=[task1.id])
    response = client.post(url, {"content": "Hi, another comment"}, follow=True)

    assert "Hi, another comment" in response.content.decode()
    # New admin shows up as "by" comment
    assert admin2.full_name in response.content.decode()

    # Try to post a comment after it's done
    task1.completed = True
    task1.save()

    response = client.post(url, {"content": "third comment"}, follow=True)
    assert response.status_code == 404

    url = reverse("admin_tasks:detail", args=[task1.id])
    response = client.get(url)

    # Comment is not shown or saved
    assert "third comment" not in response.content.decode()


@pytest.mark.django_db
def test_admin_task_comment_on_not_owned_task(
    client, admin_factory, admin_task_factory, mailoutbox
):
    admin1 = admin_factory()
    admin2 = admin_factory()
    client.force_login(admin1)

    task1 = admin_task_factory(assigned_to=admin2)

    url = reverse("admin_tasks:comment", args=[task1.id])
    client.post(url, {"content": "Hi, this is a new comment"}, follow=True)

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Someone added something to task: " + task1.name
    assert len(mailoutbox[0].to) == 1
    assert mailoutbox[0].to[0] == admin2.email
    assert admin2.first_name in mailoutbox[0].alternatives[0][0]
    assert admin1.full_name in mailoutbox[0].alternatives[0][0]
    assert "Hi, this is a new comment" in mailoutbox[0].alternatives[0][0]
