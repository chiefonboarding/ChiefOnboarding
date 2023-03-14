from django_q.tasks import async_task
from rest_framework import generics

from admin.sequences.models import Sequence
from organization.models import Notification, Organization
from slack_bot.tasks import link_slack_users
from users.emails import email_new_admin_cred
from users.models import User

from .serializers import EmployeeSerializer, SequenceSerializer, UserSerializer


class UserView(generics.CreateAPIView):
    """
    API endpoint that allows users to be created
    """

    serializer_class = UserSerializer

    def perform_create(self, serializer):
        sequences = serializer.validated_data.pop("sequences", None)
        # Default back to the organization timezone if not provided
        role = serializer.validated_data["role"]
        org = Organization.object.get()
        serializer.validated_data["timezone"] = serializer.validated_data.get(
            "timezone", org.timezone
        )
        serializer.validated_data["language"] = serializer.validated_data.get(
            "language", org.language
        )
        if role == 0:
            serializer.validated_data["start_day"] = serializer.validated_data.get(
                "start_day", org.current_datetime.date()
            )

        user = serializer.save()

        if role == 0:
            # Add sequences to new hire
            if sequences is not None:
                sequences = Sequence.objects.filter(id__in=sequences)
                user.add_sequences(sequences)

            # Send credentials email if the user was created after their start day
            org = Organization.object.get()
            new_hire_datetime = user.get_local_time()
            if (
                new_hire_datetime.date() >= user.start_day
                and new_hire_datetime.hour >= 7
                and new_hire_datetime.weekday() < 5
                and org.new_hire_email
            ):
                async_task(
                    "users.tasks.send_new_hire_credentials",
                    user.id,
                    task_name=f"Send login credentials: {user.full_name}",
                )

            # Linking user in Slack and sending welcome message (if exists)
            link_slack_users([user])
            # Update user total todo items
            user.update_progress()

            notification_type = "added_new_hire"
        if role in [1, 2]:
            async_task(
                email_new_admin_cred,
                user,
                task_name=f"Send login credentials: {user.full_name}",
            )
            if role == 1:
                notification_type = "added_administrator"
            else:
                notification_type = "added_manager"

        Notification.objects.create(
            notification_type=notification_type,
            extra_text=user.full_name,
            created_by=self.request.user,
            created_for=user,
        )


class EmployeeView(generics.ListAPIView):
    """
    API endpoint that lists all employees
    """

    queryset = User.objects.all().order_by("id")
    serializer_class = EmployeeSerializer


class SequenceView(generics.ListAPIView):
    """
    API endpoint that lists all sequences
    """

    queryset = Sequence.objects.all().order_by("id")
    serializer_class = SequenceSerializer
