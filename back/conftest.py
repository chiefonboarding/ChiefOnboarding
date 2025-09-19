import os

import pytest
from pytest_factoryboy import register

from admin.admin_tasks.factories import AdminTaskFactory
from admin.appointments.factories import AppointmentFactory
from admin.badges.factories import BadgeFactory
from admin.hardware.factories import HardwareFactory
from admin.integrations.factories import (
    CustomIntegrationFactory,
    CustomUserImportIntegrationFactory,
    IntegrationFactory,
    ManualUserProvisionIntegrationFactory,
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
    ConditionIntegrationsRevokedFactory,
    ConditionTimedFactory,
    ConditionToDoFactory,
    ConditionWithItemsFactory,
    IntegrationConfigFactory,
    OffboardingSequenceFactory,
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
    IntegrationUserFactory,
    ManagerFactory,
    NewHireFactory,
    NewHireWelcomeMessageFactory,
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
register(NewHireWelcomeMessageFactory)
register(WelcomeMessageFactory)
register(ToDoFactory)
register(ToDoUserFactory)
register(ResourceFactory)
register(ResourceUserFactory)
register(AdminTaskFactory)
register(ToDoFactory)
register(HardwareFactory)
register(AppointmentFactory)
register(IntroductionFactory)
register(NoteFactory)
register(NotificationFactory)
register(PreboardingFactory)
register(PreboardingUserFactory)
register(SequenceFactory)
register(OffboardingSequenceFactory)
register(ConditionTimedFactory)
register(ConditionToDoFactory)
register(ConditionAdminTaskFactory)
register(ConditionIntegrationsRevokedFactory)
register(PendingAdminTaskFactory)
register(PendingEmailMessageFactory)
register(PendingSlackMessageFactory)
register(PendingTextMessageFactory)
register(BadgeFactory)
register(IntegrationFactory)
register(IntegrationUserFactory)
register(CustomIntegrationFactory)
register(CustomUserImportIntegrationFactory)
register(IntegrationConfigFactory)
register(ManualUserProvisionIntegrationFactory)
register(ConditionWithItemsFactory)
register(FileFactory)
register(ResourceWithLevelDeepChaptersFactory)
register(ChapterFactory)
