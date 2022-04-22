import os

import pytest
from pytest_factoryboy import register

from admin.admin_tasks.factories import AdminTaskFactory
from admin.appointments.factories import AppointmentFactory
from admin.introductions.factories import IntroductionFactory
from admin.notes.factories import NoteFactory
from admin.preboarding.factories import PreboardingFactory
from admin.resources.factories import ResourceFactory
from admin.to_do.factories import ToDoFactory
from organization.factories import (
    NotificationFactory,
    OrganizationFactory,
    WelcomeMessageFactory,
)
from users.factories import (
    AdminFactory,
    DepartmentFactory,
    EmployeeFactory,
    ManagerFactory,
    NewHireFactory,
    NewHireWelcomeMessageFactory,
    OTPRecoveryKeyFactory,
    PreboardingUserFactory,
    ResourceUserFactory,
    ToDoUserFactory,
)


@pytest.fixture(autouse=True)
def run_around_tests():
    OrganizationFactory()
    # Generate some welcome messages for various emails
    for i in range(4):
        WelcomeMessageFactory(message_type=i, language="en")

    # Fix warning related to whitenoise
    if not os.path.exists(os.getcwd() + "/staticfiles/"):
        os.makedirs(os.getcwd() + "/staticfiles/")

    yield


register(DepartmentFactory)
register(NewHireFactory)
register(AdminFactory)
register(ManagerFactory)
register(EmployeeFactory)
register(OTPRecoveryKeyFactory)
register(NewHireWelcomeMessageFactory)
register(ToDoFactory)
register(ToDoUserFactory)
register(ResourceFactory)
register(ResourceUserFactory)
register(AdminTaskFactory)
register(ToDoFactory)
register(AppointmentFactory)
register(IntroductionFactory)
register(NoteFactory)
register(NotificationFactory)
register(PreboardingFactory)
register(PreboardingUserFactory)
