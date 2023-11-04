from django.contrib.auth import get_user_model

from admin.integrations.models import Integration
from admin.integrations.sync_userinfo import SyncUsers


def retry_integration(new_hire_id, integration_id, params):
    integration = Integration.objects.get(id=integration_id)
    new_hire = get_user_model().objects.get(id=new_hire_id)
    integration.execute(new_hire, params)


def sync_user_info(integration_id):
    # Depending on the manifest, we wil either sync specific info with the current
    # users or we will add new users. This is done in the background.
    integration = Integration.objects.get(id=integration_id)
    SyncUsers(integration).run()
