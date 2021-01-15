import pytest
from users.models import *
from resources.models import *
from freezegun import freeze_time
import datetime
from organization.models import Organization
from resources.models import Resource, Chapter
from misc.models import Content

@pytest.fixture
def resource():
    res = Resource.objects.create(name='Test chapter', course=True)
    content = Content.objects.create(type='p', content='Test content')
    chapter = Chapter.objects.create(resource=res, name='Test chapter', type=0)
    chapter.content.add(content)
    chapter2 = Chapter.objects.create(resource=res, name='Test chapter2', type=0)
    chapter2.content.add(content)
    return res

@pytest.mark.django_db
def test_create_new_hire():
    user = User.objects.create_new_hire('john', 'smith', 'JOHN@example.com', 'johnpassword')
    assert user.role == 0
    assert User.objects.count() == 1
    assert user.email == 'john@example.com'

@pytest.mark.django_db
def test_create_admin():
    user = User.objects.create_admin('jane', 'smith', 'jane@example.com', 'johnpassword')
    assert user.role == 1
    assert User.objects.count() == 1

@pytest.mark.django_db
def test_create_manager():
    user = User.objects.create_manager('jane', 'smith', 'jane@example.com', 'johnpassword')
    assert user.role == 2
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_workday():
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = User.objects.create_new_hire('john', 'smith', 'JOHN@example.com', 'johnpassword', start_day=datetime.datetime.today().date())
    freezer.stop()
    print('created new hire')
    # Freeze on the Monday
    freezer = freeze_time("2021-01-11")
    freezer.start()
    assert user.workday() == 0
    freezer.stop()

    # First day
    freezer = freeze_time("2021-01-12")
    freezer.start()
    assert user.workday() == 1
    freezer.stop()

    # Second day
    freezer = freeze_time("2021-01-13")
    freezer.start()
    assert user.workday() == 2
    freezer.stop()

    # Crossing weekend
    freezer = freeze_time("2021-01-18")
    freezer.start()
    assert user.workday() == 5
    freezer.stop()


@pytest.mark.django_db
def test_days_before_starting():
    # Set start day on Tuesday
    freezer = freeze_time("2021-01-12")
    freezer.start()
    user = User.objects.create_new_hire('john', 'smith', 'JOHN@example.com', 'johnpassword', start_day=datetime.datetime.today().date())
    freezer.stop()

    # Freeze on the Monday
    freezer = freeze_time("2021-01-11")
    freezer.start()
    assert user.days_before_starting() == 1
    freezer.stop()

    # 4 days before user starts (including weekend)
    freezer = freeze_time("2021-01-08")
    freezer.start()
    assert user.days_before_starting() == 4
    freezer.stop()

    # Once new hire has started
    freezer = freeze_time("2021-01-13")
    freezer.start()
    assert user.days_before_starting() == 0
    freezer.stop()


@pytest.mark.django_db
def test_personalize():
    manager = User.objects.create_manager('jane', 'smith', 'jane@example.com', 'johnpassword')
    new_hire = User.objects.create_new_hire('john', 'smith', 'JOHN@example.com', 'johnpassword', position='developer', manager=manager)

    text = 'Hello {{ first_name }} {{ last_name }}, your manager is {{ manager }} and you will be our {{ position }}'
    text_without_spaces = 'Hello {{first_name}} {{last_name}}, your manager is {{manager}} and you will be our {{position}}'

    expected_output = 'Hello john smith, your manager is jane smith and you will be our developer'

    assert new_hire.personalize(text) == expected_output
    assert new_hire.personalize(text_without_spaces) == expected_output

@pytest.mark.django_db
def test_resource_user(resource):
    user = User.objects.create_new_hire('john', 'smith', 'john@example.com', 'johnpassword')
    resource_user = ResourceUser.objects.create(user=user, resource=resource)
    
    resource_user.add_step(resource.chapters.first())

    assert resource_user.completed_course == False
    assert resource_user.step == 0
    assert resource_user.is_course() == True

    resource_user.add_step(resource.chapters.all()[1])

    # completed course
    assert resource_user.completed_course == True
    assert resource_user.step == 1
    assert resource_user.is_course() == False



































