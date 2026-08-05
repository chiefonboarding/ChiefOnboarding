from admin.integrations.models import Integration
from admin.sequences.models import Sequence


def assign_offboarding_sequences(user, sequence_ids):
    for integration in Integration.objects.filter(
        manifest_type=Integration.ManifestType.WEBHOOK,
        manifest__exists__isnull=False,
    ):
        integration.user_exists(user)

    sequences = Sequence.offboarding.filter(id__in=sequence_ids)
    user.add_sequences(sequences)
