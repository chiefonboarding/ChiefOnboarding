import pytest

from organization.factories import OrganizationFactory


@pytest.fixture(autouse=True)
def run_around_tests():
    OrganizationFactory()

    yield
