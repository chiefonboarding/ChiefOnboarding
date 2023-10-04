import os

import pytest
from pytest_factoryboy import register

from admin.admin_tasks.factories import AdminTaskFactory
from admin.appointments.factories import AppointmentFactory
from admin.badges.factories import BadgeFactory
from admin.integrations.factories import (
    CustomIntegrationFactory,
    CustomUserImportIntegrationFactory,
    IntegrationFactory,
)
from admin.introductions.factories import IntroductionFactory
from admin.notes.factories import NoteFactory
from admin.preboarding.factories import PreboardingFactory
from admin.resources.factories import (
    ChapterFactory,
    ResourceFactory,
    ResourceWithLevelDeepChaptersFactory,
)
from admin.sequences.factories import (
    ConditionAdminTaskFactory,
    ConditionTimedFactory,
    ConditionToDoFactory,
    ConditionWithItemsFactory,
    IntegrationConfigFactory,
    PendingAdminTaskFactory,
    PendingEmailMessageFactory,
    PendingSlackMessageFactory,
    PendingTextMessageFactory,
    SequenceFactory,
)
from admin.to_do.factories import ToDoFactory
from misc.factories import FileFactory
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
def run_around_tests(request, settings):
    if request.node.get_closest_marker("no_run_around_tests"):
        yield
        return
    settings.FAKE_SLACK_API = True
    settings.SLACK_APP_TOKEN = ""
    OrganizationFactory(id=1)

    # Generate some welcome messages for various emails
    for i in range(5):
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
register(WelcomeMessageFactory)
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
register(SequenceFactory)
register(ConditionTimedFactory)
register(ConditionToDoFactory)
register(ConditionAdminTaskFactory)
register(PendingAdminTaskFactory)
register(PendingEmailMessageFactory)
register(PendingSlackMessageFactory)
register(PendingTextMessageFactory)
register(BadgeFactory)
register(IntegrationFactory)
register(CustomIntegrationFactory)
register(CustomUserImportIntegrationFactory)
register(IntegrationConfigFactory)
register(ConditionWithItemsFactory)
register(FileFactory)
register(ResourceWithLevelDeepChaptersFactory)
register(ChapterFactory)
