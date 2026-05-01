from admin.sequences.models import Sequence
from users.models import User


def get_sequences_for_user(*, user: User):
    return Sequence.objects.for_user(user=user)


def get_onboarding_sequences_for_user(*, user: User):
    return Sequence.onboarding.for_user(user=user)


def get_offboarding_sequences_for_user(*, user: User):
    return Sequence.offboarding.for_user(user=user)
