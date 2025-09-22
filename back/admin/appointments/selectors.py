from admin.appointments.models import Appointment
from users.models import User

def get_appointment_templates_for_user(*, user: User):
    return Appointment.templates.for_user(user=user)
