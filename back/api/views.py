from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from django_q.tasks import async_task

from admin.sequences.models import Sequence
from organization.models import Notification, Organization
from slack_bot.tasks import link_slack_users
from users.models import User

from .permissions import AdminPermission
from .serializers import EmployeeSerializer, SequenceSerializer, UserSerializer


class UserView(generics.CreateAPIView):
    """
    API endpoint that allows new hires to be created
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        AdminPermission,
    ]
    authentication_classes = [
        TokenAuthentication,
    ]

    def perform_create(self, serializer):
        sequences = serializer.pop("sequences")
        sequences = Sequence.objects.filter(id__in=sequences)

        new_hire = serializer.save(role=1)

        # Add sequences to new hire
        new_hire.add_sequences(sequences)

        # Send credentials email if the user was created after their start day
        org = Organization.object.get()
        new_hire_datetime = new_hire.get_local_time()
        if (
            new_hire_datetime.date() >= new_hire.start_day
            and new_hire_datetime.hour >= 7
            and new_hire_datetime.weekday() < 5
            and org.new_hire_email
        ):
            async_task(
                "users.tasks.send_new_hire_credentials",
                new_hire.id,
                task_name=f"Send login credentials: {new_hire.full_name}",
            )

        # Linking user in Slack and sending welcome message (if exists)
        link_slack_users([new_hire])

        Notification.objects.create(
            notification_type="added_new_hire",
            extra_text=new_hire.full_name,
            created_by=self.request.user,
            created_for=new_hire,
        )

        # Update user total todo items
        new_hire.update_progress()


class EmployeeView(generics.ListAPIView):
    """
    API endpoint that lists all employees
    """

    queryset = User.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [
        AdminPermission,
    ]
    authentication_classes = [
        TokenAuthentication,
    ]


class SequenceView(generics.ListAPIView):
    """
    API endpoint that lists all sequences
    """

    queryset = Sequence.objects.all()
    serializer_class = SequenceSerializer
    permission_classes = [
        AdminPermission,
    ]
    authentication_classes = [
        TokenAuthentication,
    ]
