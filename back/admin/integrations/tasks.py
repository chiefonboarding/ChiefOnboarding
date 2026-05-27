import logging

from django.contrib.auth import get_user_model
from django_q.tasks import async_task

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


def refresh_access_for_user_integration(integration_id, user_id):
    # One `exists` lookup for a single (integration, user) pair. Enqueued
    # individually so a slow or failing integration can't stall the whole
    # refresh. Errors are swallowed and logged — one bad lookup must not
    # prevent the other queued tasks from running.
    try:
        integration = Integration.objects.get(id=integration_id)
        user = get_user_model().objects.get(id=user_id)
    except (Integration.DoesNotExist, get_user_model().DoesNotExist):
        return
    try:
        integration.user_exists(user, save_result=True)
    except Exception as e:
        logger.warning(
            "Refresh error for integration %s, user %s: %s",
            integration_id, user.email, e,
        )


def refresh_access_report():
    # Enqueue one background task per (integration, user) pair instead of
    # running every lookup inline — a single big task was timing out on
    # orgs with lots of staff. The worker pool processes the queue, which
    # also provides natural throttling against per-service rate limits.
    User = get_user_model()
    integrations = (
        Integration.objects.account_provision_options().filter(is_active=True)
    )
    user_ids = list(
        User.objects.filter(is_active=True)
        .exclude(email="")
        .order_by("id")
        .values_list("id", flat=True)
    )

    enqueued = 0
    for integration in integrations:
        # Manual-provisioning integrations don't make HTTP calls; their
        # IntegrationUser rows only change via the toggle button. Skip them.
        if integration.skip_user_provisioning:
            continue
        for user_id in user_ids:
            async_task(
                "admin.integrations.tasks.refresh_access_for_user_integration",
                integration.id,
                user_id,
                task_name=f"Refresh access: {integration.name} #{user_id}",
            )
            enqueued += 1

    logger.info("Access report refresh enqueued: %s tasks", enqueued)
    return {"enqueued": enqueued}
