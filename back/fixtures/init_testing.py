from organization.models import Organization
from users.models import User
Organization.objects.create(name="<organization name>")
User.objects.create_admin("<first name>", "<last name>", "<email>", "<password>")
