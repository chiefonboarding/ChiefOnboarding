from django.contrib.auth import get_user_model

from admin.integrations.models import Integration
from admin.integrations.sync_userinfo import SyncUsers


def retry_integration(new_hire_id, integration_id, params):
    integration = Integration.objects.get(id=integration_id)
    new_hire = get_user_model().objects.get(id=new_hire_id)
    integration.execute(new_hire, params)


def sync_user_info(integration):
    # this will sync the information from a third party to the new hires only used
    # when we need info from the new hire that is only available in list view
    # for example, some apis only allow lookups based on their internal ID of a
    # user. We do not have that ID yet, but we need it so we can sync it with this.

    # user is not relevant here, so just pick any
    SyncUsers(integration).sync_user_info()
