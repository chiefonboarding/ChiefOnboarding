import logging

from django.contrib.auth import get_user_model

from admin.integrations.models import Integration
from admin.integrations.sync_userinfo import SyncUsers

logger = logging.getLogger(__name__)


def retry_integration(new_hire_id, integration_id, params):
    integration = Integration.objects.get(id=integration_id)
    new_hire = get_user_model().objects.get(id=new_hire_id)
    integration.execute(new_hire, params)


def sync_user_info(integration_id):
    # Depending on the manifest, we wil either sync specific info with the current
    # users or we will add new users. This is done in the background.
    integration = Integration.objects.get(id=integration_id)
    SyncUsers(integration).run()


def backfill_integration_ids(integration_id):
    # Run the integration's `exists` lookup against every user. Any
    # store_data fields declared on the exists block get written to the
    # user's extra_fields. Used to populate IDs for users who were
    # provisioned in the external system before this integration existed.
    integration = Integration.objects.get(id=integration_id)
    store_keys = list(
        integration.manifest.get("exists", {}).get("store_data", {}).keys()
    )

    users = get_user_model().objects.exclude(email="").order_by("id")
    matched = skipped = not_found = errored = 0

    for user in users:
        # skip users who already have all backfill keys set
        if store_keys and all(k in user.extra_fields for k in store_keys):
            skipped += 1
            continue
        try:
            result = integration.user_exists(user, save_result=False)
        except Exception as e:
            logger.warning(
                "Backfill error for integration %s, user %s: %s",
                integration_id, user.email, e,
            )
            errored += 1
            continue
        if result is True:
            matched += 1
        elif result is False:
            not_found += 1
        else:
            errored += 1

    logger.info(
        "Backfill complete for integration %s: "
        "%s matched, %s skipped, %s not found, %s errored",
        integration_id, matched, skipped, not_found, errored,
    )
    return {
        "matched": matched,
        "skipped": skipped,
        "not_found": not_found,
        "errored": errored,
    }
