import pytest

from organization.factories import OrganizationFactory, WelcomeMessageFactory


@pytest.fixture(autouse=True)
def run_around_tests():
    OrganizationFactory()
    # Generate some welcome messages for various emails
    for i in range(4):
        WelcomeMessageFactory(message_type=i, language="en")

    yield
