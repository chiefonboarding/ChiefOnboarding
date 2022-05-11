from organization.models import Organization
from users.models import User

Organization.objects.create(name="<organization name>")
User.objects.create(
    first_name="<first_name>",
    last_name="<last_name>",
    email="<email>",
    password="<password>"
)
