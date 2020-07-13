from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import ResourceUser, NewHireWelcomeMessage
from appointments.serializers import AppointmentSerializer
from preboarding.serializers import PreboardingSerializer
from resources.serializers import ResourceSerializer
from to_do.serializers import ToDoSerializer
from introductions.serializers import IntroductionSerializer
from badges.serializers import BadgeSerializer
from misc.serializers import FileSerializer
from misc.models import File
from resources.models import Resource

from resources.serializers import CourseAnswerSerializer, ChapterCourseSerializer
from resources.serializers import ChapterSerializer


class BaseUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    full_name = serializers.SerializerMethodField()
    has_to_do = serializers.SerializerMethodField()
    has_resources = serializers.SerializerMethodField()
    slack_user_id = serializers.CharField(read_only=True)
    slack_channel_id = serializers.CharField(read_only=True)

    def validate(self, value):
        users_with_same_email = get_user_model().objects.filter(email=value['email'].lower().strip())
        if self.instance:
            users_with_same_email = users_with_same_email.exclude(id=self.instance.id)
        if users_with_same_email.exists():
            raise serializers.ValidationError("user with this email already exists.")
        return value

    class Meta:
        model = get_user_model()
        exclude = ('conditions', 'preboarding', 'appointments', 'introductions', 'to_do', 'resources', 'badges')
        # fields = '__all__'

    def get_full_name(self, obj):
        return obj.first_name + ' ' + obj.last_name

    def get_has_to_do(self, obj):
        return obj.to_do.count() > 0

    def get_has_resources(self, obj):
        return obj.resources.count() > 0


class NewHireSerializer(BaseUserSerializer):
    search_type = serializers.CharField(default='new_hire', read_only=True)
    role = serializers.IntegerField(read_only=True)
    # badges = BadgeSerializer(read_only=True, many=True)

    def create(self, validated_data):
        user = get_user_model().objects.create_new_hire(**validated_data)
        return user


class AdminSerializer(BaseUserSerializer):
    search_type = serializers.CharField(default='admin', read_only=True)


class EmployeeSerializer(BaseUserSerializer):
    search_type = serializers.CharField(default='employee', read_only=True)
    slack_loading = serializers.BooleanField(default=False, read_only=True)
    email_loading = serializers.BooleanField(default=False, read_only=True)
    role = serializers.IntegerField(default='3', read_only=True)
    name = serializers.SerializerMethodField()
    has_pwd = serializers.SerializerMethodField()
    profile_image = FileSerializer(read_only=True)
    profile_image_id = serializers.PrimaryKeyRelatedField(
        source='profile_image',
        queryset=File.objects.all(),
        required=False
    )

    class Meta:
        model = get_user_model()
        fields = ('id', 'first_name', 'last_name', 'email', 'position', 'phone', 'full_name', 'slack_user_id',
                  'has_pwd', 'search_type', 'twitter', 'facebook', 'linkedin', 'message', 'profile_image',
                  'profile_image_id', 'name', 'role', 'slack_loading', 'email_loading')

    def get_has_pwd(self, obj):
        return obj.password != ''

    def get_name(self, obj):
        return obj.first_name + ' ' + obj.last_name


class UserLanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = get_user_model()
        fields = ('language',)


class TaskSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    to_do = ToDoSerializer(many=True, read_only=True)
    introductions = IntroductionSerializer(many=True, read_only=True)
    appointments = AppointmentSerializer(many=True, read_only=True)
    preboarding = PreboardingSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ('preboarding', 'to_do', 'resources', 'introductions', 'appointments')


class ResourceProgressSerializer(serializers.ModelSerializer):
    amount_resources = serializers.SerializerMethodField()
    resources = ChapterSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = ('amount_resources', 'name', 'resources')

    def get_amount_resources(self, obj):
        return obj.chapters.count()


class NewHireProgressResourceSerializer(serializers.ModelSerializer):
    resource = ResourceProgressSerializer()
    answers = CourseAnswerSerializer(read_only=True, many=True)

    class Meta:
        model = ResourceUser
        fields = ('id', 'resource', 'step', 'answers', 'reminded', 'completed_course')


class NewHireWelcomeMessageSerializer(serializers.ModelSerializer):
    colleague = EmployeeSerializer()

    class Meta:
        model = NewHireWelcomeMessage
        fields = ('id', 'colleague', 'message')


