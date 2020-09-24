import boto3
from botocore.config import Config
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, Tag, WelcomeMessage
from misc.models import File
from .serializers import BaseOrganizationSerializer, DetailOrganizationSerializer, \
    WelcomeMessageSerializer, ExportSerializer
from misc.serializers import FileSerializer
from users.permissions import NewHirePermission, AdminPermission
from django.core import management


def home(request):
    return render(request, 'index.html')


class OrgView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        org = BaseOrganizationSerializer(Organization.object.get())
        return Response(org.data)


class OrgDetailView(APIView):

    def get(self, request):
        org = DetailOrganizationSerializer(Organization.object.get())
        return Response(org.data)

    def patch(self, request):
        serializer = DetailOrganizationSerializer(Organization.object.get(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class WelcomeMessageView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        welcome_messages = WelcomeMessage.objects.all()
        serializer = WelcomeMessageSerializer(welcome_messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = WelcomeMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        welcome_message = WelcomeMessage.objects.get(language=serializer.data['language'], message_type=serializer.data['message_type'])
        welcome_message.message = serializer.data['message']
        welcome_message.save()
        return Response(serializer.data)


class TagView(APIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request):
        tags = [i.name for i in Tag.objects.all()]
        return Response(tags)


class CSRFTokenView(APIView):
    permission_classes = (AllowAny,)

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return HttpResponse()


class FileView(APIView):
    permission_classes = (AdminPermission, NewHirePermission)

    def get(self, request, id, uuid):
        file = get_object_or_404(File, uuid=uuid, id=id)
        url = file.get_url()
        return Response(url)

    def post(self, request):
        serializer = FileSerializer(data={'name': request.data['name'], 'ext': request.data['name'].split('.')[1]})
        serializer.is_valid(raise_exception=True)
        f = serializer.save()
        key = str(f.id) + '-' + request.data['name'].split('.')[0] + '/' + request.data['name']
        f.key = key
        f.save()

        s3 = boto3.client('s3',
                          settings.AWS_REGION,
                          endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          config=Config(signature_version='s3v4')
                          )
        url = s3.generate_presigned_url(ClientMethod='put_object', ExpiresIn=3600,
                                        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key})
        return Response({'url': url, 'id': f.id})

    def put(self, request, id):
        file = get_object_or_404(File, pk=id)
        file.active = True
        file.save()
        return Response(FileSerializer(file).data)

    def delete(self, request, id):
        if request.user.role == 1:
            file = get_object_or_404(File, pk=id)
            file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoView(APIView):

    def put(self, request, id):
        file = get_object_or_404(File, pk=id)
        file.active = True
        file.save()
        org = Organization.object.get()
        org.logo = file
        org.save()
        return Response(FileSerializer(file).data)


class ExportView(APIView):

    def post(self, request):
        from io import StringIO
        import json
        from django.core.files.base import ContentFile
        buf = StringIO()
        serializer = ExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        management.call_command('dumpdata', serializer.data['export_model'], stdout=buf, natural_foreign=True)
        buf.seek(0)
        return Response(json.loads(buf.read()))
