import datetime

import pytest
from django.contrib import auth
from django.urls import reverse
from freezegun import freeze_time

from admin.admin_tasks.models import AdminTask
from organization.models import Notification
from users.models import ToDoUser


@pytest.mark.django_db
@freeze_time("2021-01-12")
def test_show_to_do_view(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(
        start_day=datetime.datetime.fromisoformat("2021-01-12").date()
    )
    client.force_login(new_hire)

    url = reverse("new_hire:todos")

    to_do_item1 = to_do_user_factory(to_do__due_on_day=1, user=new_hire)
    to_do_item2 = to_do_user_factory(to_do__due_on_day=1, user=new_hire)
    to_do_item3 = to_do_user_factory(to_do__due_on_day=2, user=new_hire)
    to_do_item4 = to_do_user_factory(to_do__due_on_day=5, user=new_hire)
    to_do_item5 = to_do_user_factory(to_do__due_on_day=5, user=new_hire)

    # Should not be considered - different user
    to_do_item6 = to_do_user_factory(to_do__due_on_day=2)

    to_do_items = [
        to_do_item1.to_do,
        to_do_item2.to_do,
        to_do_item3.to_do,
        to_do_item4.to_do,
        to_do_item5.to_do,
    ]

    response = client.get(url)

    assert len(response.context["to_do_items"]) == 3

    expected_days = [1, 2, 5]
    expected_dates = ["2021-01-12", "2021-01-13", "2021-01-18"]
    expected_to_do_items = [
        [to_do_item1, to_do_item2],
        [to_do_item3],
        [to_do_item4, to_do_item5],
    ]

    for idx, item in enumerate(response.context["to_do_items"]):
        assert expected_days[idx] == item["day"]
        assert expected_dates[idx] == str(item["date"])
        assert expected_to_do_items[idx] == item["items"]

    # All items are shown
    for to_do in to_do_items:
        assert to_do.name in response.content.decode()

    # Different user, not shown
    assert to_do_item6.to_do.name not in response.content.decode()

    # No overdue tasks
    assert "Overdue" not in response.content.decode()


@pytest.mark.django_db
@freeze_time("2021-01-13")
def test_show_over_due_to_do_view(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory(
        start_day=datetime.datetime.fromisoformat("2021-01-12").date()
    )
    client.force_login(new_hire)

    url = reverse("new_hire:todos")

    # overdue
    to_do_item1 = to_do_user_factory(to_do__due_on_day=1, user=new_hire)
    # not overdue
    to_do_item2 = to_do_user_factory(to_do__due_on_day=2, user=new_hire)

    response = client.get(url)

    assert len(response.context["overdue_to_do_items"]) == 1
    assert response.context["overdue_to_do_items"][0] == to_do_item1

    assert "Overdue" in response.content.decode()
    assert len(response.context["to_do_items"]) == 1
    assert response.context["to_do_items"][0]["items"][0] == to_do_item2


@pytest.mark.django_db
def test_to_do_item_view(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    to_do_item1 = to_do_user_factory(user=new_hire)

    url = reverse(
        "new_hire:to_do",
        args=[
            to_do_item1.id,
        ],
    )

    response = client.get(url)

    assert to_do_item1.to_do.name in response.content.decode()
    assert "Please complete this item!" in response.content.decode()
    assert "I have completed this item!" in response.content.decode()


@pytest.mark.django_db
def test_to_do_item_not_owner_view(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    to_do_item1 = to_do_user_factory()
    # Not owner of item, so should not show
    url = reverse(
        "new_hire:to_do",
        args=[
            to_do_item1.id,
        ],
    )
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_to_do_item_completed_view(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    # Completed item
    to_do_item1 = to_do_user_factory(user=new_hire, completed=True)

    url = reverse(
        "new_hire:to_do",
        args=[
            to_do_item1.id,
        ],
    )
    response = client.get(url)

    assert "You have already completed this item" in response.content.decode()


@pytest.mark.django_db
def test_complete_to_do_item_view(
    client,
    new_hire_factory,
    to_do_user_factory,
):
    new_hire = new_hire_factory()
    to_do_user = to_do_user_factory(user=new_hire)
    client.force_login(new_hire)

    url = reverse(
        "new_hire:to_do_complete",
        args=[
            to_do_user.id,
        ],
    )
    response = client.post(url, follow=True)

    to_do_user.refresh_from_db()

    assert response.status_code == 200
    assert to_do_user.completed


@pytest.mark.django_db
def test_complete_to_do_item_view_with_trigger(
    client, new_hire_factory, sequence_factory, condition_with_items_factory
):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    sequence = sequence_factory()
    con = condition_with_items_factory(condition_type=1, sequence=sequence)

    new_hire.add_sequences([sequence])
    # Add to do item from sequence to new hire. Once we have triggered this, all
    # other items should be added/triggered too.
    new_hire.to_do.add(con.condition_to_do.all().first())

    url = reverse(
        "new_hire:to_do_complete",
        args=[
            ToDoUser.objects.filter(user=new_hire).first().id,
        ],
    )
    client.post(url, follow=True)

    # Completed todo + 9 from condition
    assert Notification.objects.all().count() == 11
    # One failed because of no email
    assert Notification.objects.filter(notification_type="failed_no_email").count() == 1

    # Check if we got all items
    assert new_hire.to_do.all().count() == 2
    assert new_hire.resources.all().count() == 1
    assert new_hire.appointments.all().count() == 1
    assert new_hire.introductions.all().count() == 1
    assert new_hire.badges.all().count() == 1
    assert new_hire.preboarding.all().count() == 1

    assert AdminTask.objects.count() == 1


@pytest.mark.django_db
def test_complete_to_do_item_with_form_view(
    client, new_hire_factory, to_do_user_factory
):
    new_hire = new_hire_factory()
    client.force_login(new_hire)
    to_do_user = to_do_user_factory(
        user=new_hire,
        to_do__content={
            "time": 0,
            "blocks": [
                {
                    "id": "1",
                    "type": "form",
                    "data": {
                        "content": "Please answer this",
                        "type": "input",
                    },
                },
                {
                    "id": "2",
                    "type": "form",
                    "data": {
                        "content": "Please answer this too",
                        "type": "input",
                    },
                },
            ],
        },
    )

    url = reverse(
        "new_hire:to_do_form",
        args=[
            to_do_user.id,
        ],
    )
    response = client.post(
        url, data={"1": "I have answered this", "2": "this too"}, follow=True
    )

    to_do_user.refresh_from_db()

    assert len(to_do_user.to_do.form_items) == 2
    assert response.status_code == 200
    assert (
        "This form could not be processed - invalid items"
        not in response.content.decode()
    )

    assert to_do_user.form == [
        {
            "id": "1",
            "data": {
                "type": "input",
                "content": "Please answer this",
            },
            "type": "form",
            "answer": "I have answered this",
        },
        {
            "id": "2",
            "data": {
                "type": "input",
                "content": "Please answer this too",
            },
            "type": "form",
            "answer": "this too",
        },
    ]
    # send weird response
    response = client.post(
        url, data={"334": "I have answered this", "2": "this too"}, follow=True
    )
    assert (
        "This form could not be processed - invalid items" in response.content.decode()
    )


@pytest.mark.django_db
def test_preboarding_redirect_block(client, settings, new_hire_factory):
    # Set amount of tries to 3
    settings.AXES_FAILURE_LIMIT = 3

    new_hire_factory()

    url = reverse("new_hire:preboarding-url")

    response = client.get(url + "?token=test")
    assert response.status_code == 404

    response = client.get(url + "?token=test12")
    assert response.status_code == 404

    response = client.get(url + "?token=test123")
    assert response.status_code == 403
    assert "Account locked: too many login attempts." in response.content.decode()


@pytest.mark.django_db
def test_preboarding_redirect_success_no_preboarding_items(client, new_hire_factory):
    new_hire = new_hire_factory()

    url = reverse("new_hire:preboarding-url")

    response = client.get(url + "?token=" + new_hire.unique_url)
    # hitting 404 because there are no preboarding items yet
    assert response.status_code == 404

    user = auth.get_user(client)
    # User is authenticated because the url was valid
    assert user.is_authenticated


@pytest.mark.django_db
def test_preboarding_redirect_success_with_preboarding_items(
    client, preboarding_user_factory
):
    preboarding_user1 = preboarding_user_factory()
    new_hire = preboarding_user1.user

    url = reverse("new_hire:preboarding-url")

    response = client.get(url + "?token=" + new_hire.unique_url, follow=True)
    # Successful authenticate
    assert response.status_code == 200

    user = auth.get_user(client)
    # User is authenticated because the url was valid
    assert user.is_authenticated

    assert preboarding_user1.preboarding.name in response.content.decode()
    # No buttons only one preboarding item
    assert "Next" not in response.content.decode()
    assert "Restart" not in response.content.decode()

    # Add new preboardint item
    preboarding_user2 = preboarding_user_factory(user=new_hire)

    # Button is now visible
    response = client.get(url + "?token=" + new_hire.unique_url, follow=True)
    assert "Next" in response.content.decode()

    # Go to next page
    url = reverse("new_hire:preboarding", args=[response.context["next_id"]])

    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert "Restart" in response.content.decode()

    assert preboarding_user2.preboarding.name in response.content.decode()


@pytest.mark.django_db
def test_colleague_list_view(
    client,
    admin_factory,
    employee_factory,
    new_hire_factory,
    manager_factory,
    introduction_factory,
):
    admin = admin_factory()
    manager = manager_factory()
    employee = employee_factory()
    new_hire = new_hire_factory()

    client.force_login(new_hire)

    url = reverse("new_hire:colleagues")

    response = client.get(url)

    # Regardless of type, show all people on colleagues page
    assert admin.full_name in response.content.decode()
    assert manager.full_name in response.content.decode()
    assert employee.full_name in response.content.decode()
    assert new_hire.full_name in response.content.decode()

    # Adding introduction item
    intro = introduction_factory(
        intro_person__message="Hi {{first_name}}, welcome to the club!"
    )

    new_hire.introductions.add(intro)

    # Get page again
    response = client.get(url)

    assert intro.intro_person.full_name in response.content.decode()
    assert (
        f"Hi {new_hire.first_name}, welcome to the club!" in response.content.decode()
    )


@pytest.mark.django_db
def test_colleague_search_view(
    client, admin_factory, employee_factory, new_hire_factory, manager_factory
):
    admin = admin_factory(first_name="Dorian")
    manager = manager_factory(last_name="Dorian")
    employee = employee_factory()
    new_hire = new_hire_factory()

    client.force_login(new_hire)

    url = reverse("new_hire:colleagues-search")
    response = client.get(url)

    assert len(response.context["object_list"]) == 4

    response = client.get(url + "?search=rian")

    assert len(response.context["object_list"]) == 2
    assert admin.full_name in response.content.decode()
    assert manager.full_name in response.content.decode()
    assert employee.full_name not in response.content.decode()


@pytest.mark.django_db
def test_resource_list_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)
    # Not for current new hire
    resource_user1 = resource_user_factory()
    resource_user2 = resource_user_factory(user=new_hire)

    url = reverse("new_hire:resources")
    response = client.get(url)

    assert len(response.context["object_list"]) == 1
    assert resource_user2.resource.name in response.content.decode()
    assert resource_user1.resource.name not in response.content.decode()


@pytest.mark.django_db
def test_resource_search_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)
    # Not for current new hire
    resource_user1 = resource_user_factory(user=new_hire, resource__name="search this")
    resource_user2 = resource_user_factory(
        user=new_hire, resource__name="something different"
    )

    chapter = resource_user2.resource.chapters.first()
    chapter.name = "search that"
    chapter.save()

    url = reverse("new_hire:resources-search")
    response = client.get(url + "?search=search")

    assert len(response.context["results"]) == 2
    assert resource_user2.resource.name in response.content.decode().replace(
        "<b>", ""
    ).replace("</b>", "")
    assert resource_user1.resource.name in response.content.decode().replace(
        "<b>", ""
    ).replace("</b>", "")

    response = client.get(url + "?search=something+different")

    assert len(response.context["results"]) == 1
    assert resource_user1.resource.name not in response.content.decode().replace(
        "<b>", ""
    ).replace("</b>", "")


@pytest.mark.django_db
def test_resource_detail_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    resource_user1 = resource_user_factory(user=new_hire, resource__name="search this")
    url = reverse(
        "new_hire:resource-detail",
        args=[resource_user1.resource.id, resource_user1.resource.first_chapter_id],
    )
    response = client.get(url)

    assert response.status_code == 200
    # Check that chapter is selected and in the header
    assert (
        '<h3 class="card-title">'
        + resource_user1.resource.chapters.all()[0].name
        + "</h3>"
        in response.content.decode()
    )
    # Check that the title shows the name of the course
    assert (
        f'<h2 class="page-title">{resource_user1.object_name}</h2>'
        in response.content.decode()
    )
    # Both chapter titles are on the page
    assert resource_user1.resource.chapters.all()[0].name in response.content.decode()
    assert resource_user1.resource.chapters.all()[1].name in response.content.decode()

    # Get second page
    url = reverse(
        "new_hire:resource-detail",
        args=[resource_user1.resource.id, resource_user1.resource.chapters.all()[1].id],
    )
    response = client.get(url)

    # Header changed
    assert (
        '<h3 class="card-title">'
        + resource_user1.resource.chapters.all()[1].name
        + "</h3>"
        in response.content.decode()
    )


@pytest.mark.django_db
def test_course_cannot_skip_chapter_view(
    client, new_hire_factory, resource_user_factory
):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    resource_user1 = resource_user_factory(user=new_hire, resource__course=True)

    # Get second page without having visited the first one
    url = reverse(
        "new_hire:resource-detail",
        args=[resource_user1.resource.id, resource_user1.resource.chapters.all()[1].id],
    )
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_course_cannot_open_non_assigned_course(
    client, new_hire_factory, resource_user_factory
):
    new_hire = new_hire_factory()
    client.force_login(new_hire)
    # Not for this user
    resource_user2 = resource_user_factory(resource__course=True)

    # Can't open this as user has no access to the resource
    url = reverse(
        "new_hire:resource-detail",
        args=[resource_user2.resource.id, resource_user2.resource.first_chapter_id],
    )
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_course_show_questions_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    resource_user1 = resource_user_factory(user=new_hire, resource__course=True, step=2)
    chapter = resource_user1.resource.chapters.all()[1]
    chapter.order = 1
    chapter.save()

    url = reverse(
        "new_hire:resource-detail", args=[resource_user1.resource.id, chapter.id]
    )

    response = client.get(url)

    # Form is now available
    assert "form" in response.context

    assert "Please answer this question" in response.content.decode()
    assert "first option" in response.content.decode()
    assert "second option" in response.content.decode()


@pytest.mark.django_db
def test_course_next_step_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    resource_user1 = resource_user_factory(user=new_hire, resource__course=True)

    chapter = resource_user1.resource.chapters.all()[0]
    chapter.order = 0
    chapter.save()

    chapter = resource_user1.resource.chapters.all()[1]
    chapter.order = 1
    chapter.save()

    url = reverse(
        "new_hire:resource-detail",
        args=[resource_user1.resource.id, resource_user1.resource.first_chapter_id],
    )
    response = client.get(url)

    # Next button has correct link
    assert (
        reverse("new_hire:course-next-step", args=[resource_user1.id])
        in response.content.decode()
    )

    # Click that button
    url = reverse("new_hire:course-next-step", args=[resource_user1.id])
    response = client.post(url, follow=True)

    resource_user1.refresh_from_db()

    # New url is next page
    assert response.redirect_chain[-1][0] == reverse(
        "new_hire:resource-detail", args=[resource_user1.resource.id, chapter.id]
    )

    # Step has been increased
    assert resource_user1.step == 1

    # Go to the next page (does not exist - current is last one)
    response = client.post(url, follow=True)

    assert "You have completed this course!" in response.content.decode()
    assert response.redirect_chain[-1][0] == reverse("new_hire:resources")


@pytest.mark.django_db
def test_course_form_view(client, new_hire_factory, resource_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)

    resource_user1 = resource_user_factory(user=new_hire, resource__course=True, step=0)

    chapter = resource_user1.resource.chapters.all()[0]
    chapter.order = 0
    chapter.save()

    chapter = resource_user1.resource.chapters.all()[1]
    chapter.order = 1
    chapter.save()

    # No access to this yet, because we haven't hit the first page yet. Should always
    # return 404
    url = reverse(
        "new_hire:question-form", args=[resource_user1.resource.id, chapter.id]
    )
    response = client.get(url)

    assert response.status_code == 404

    response = client.post(url)

    assert response.status_code == 404

    # Force user to second page
    resource_user1.step = 1
    resource_user1.save()

    # Load form
    response = client.get(url)

    # Form is shown
    assert "Please answer this question" in response.content.decode()
    # No answers yet
    assert resource_user1.answers.all().count() == 0

    # Post to form
    response = client.post(url, data={"item-0": "2"}, follow=True)

    assert response.status_code == 200

    resource_user1.refresh_from_db()

    # We got an answer
    assert resource_user1.answers.all().count() == 1
    assert resource_user1.answers.all().first().answers == {"item-0": "2"}


@pytest.mark.django_db
def test_seen_notifications(client, new_hire_factory):
    new_hire = new_hire_factory()
    new_hire.seen_updates = datetime.datetime.now() - datetime.timedelta(days=2)
    new_hire.save()
    client.force_login(new_hire)

    current_date_time = datetime.datetime.now()
    assert new_hire.seen_updates.day != current_date_time.day

    url = reverse("new_hire:seen-updates")
    response = client.get(url)

    new_hire.refresh_from_db()
    assert response.status_code == 200

    assert new_hire.seen_updates.day == current_date_time.day


@pytest.mark.django_db
def test_slack_to_do_webpage_block(client, settings, new_hire_factory, to_do_factory):
    # Set amount of tries to 3
    settings.AXES_FAILURE_LIMIT = 3

    new_hire_factory()
    to_do = to_do_factory()

    url = reverse("new_hire:slack_to_do", args=[to_do.id])

    response = client.get(url + "?token=test")
    assert response.status_code == 404

    response = client.get(url + "?token=test12")
    assert response.status_code == 404

    response = client.get(url + "?token=test123")
    assert response.status_code == 403
    assert "Account locked: too many login attempts." in response.content.decode()


@pytest.mark.django_db
def test_slack_to_do_webpage(client, new_hire_factory, to_do_user_factory):
    new_hire = new_hire_factory()
    client.force_login(new_hire)
    to_do_user = to_do_user_factory(
        user=new_hire,
        to_do__content={
            "time": 0,
            "blocks": [
                {
                    "id": "1",
                    "type": "form",
                    "data": {
                        "content": "Please answer this",
                        "type": "text",
                    },
                },
                {
                    "id": "2",
                    "type": "header",
                    "data": {
                        "content": "Random header",
                        "level": "2",
                    },
                },
                {
                    "id": "3",
                    "type": "form",
                    "data": {
                        "content": "Please answer this too",
                        "type": "input",
                    },
                },
            ],
        },
    )

    url = reverse("new_hire:slack_to_do", args=[to_do_user.to_do.id])

    response = client.get(url + "?token=" + new_hire.unique_url)

    assert response.status_code == 200
