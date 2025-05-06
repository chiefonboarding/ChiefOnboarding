import boto3
import os
from botocore.config import Config
from django.conf import settings

from .local_s3 import LocalS3Storage


class S3:
    def __init__(self):
        # Get settings from database if available
        from organization.models import Organization

        try:
            org = Organization.object.get()

            # Check if S3 is configured in the database
            if org.storage_provider == 's3' and org.s3_bucket_name:
                # Use S3 settings from database
                self.use_s3 = True

                # Set environment variables for boto3
                os.environ['AWS_S3_ENDPOINT_URL'] = org.s3_endpoint_url
                os.environ['AWS_ACCESS_KEY_ID'] = org.s3_access_key
                os.environ['AWS_SECRET_ACCESS_KEY'] = org.s3_secret_key
                os.environ['AWS_STORAGE_BUCKET_NAME'] = org.s3_bucket_name
                os.environ['AWS_DEFAULT_REGION'] = org.s3_region

                # Use actual S3
                self.client = boto3.client(
                    "s3",
                    org.s3_region,
                    endpoint_url=org.s3_endpoint_url,
                    config=Config(signature_version="s3v4"),
                    aws_access_key_id=org.s3_access_key,
                    aws_secret_access_key=org.s3_secret_key,
                )
                return
        except Exception:
            # If there's any error, fall back to environment settings
            pass

        # Fall back to environment settings if database settings are not available
        # Check if S3 is configured in environment
        self.use_s3 = settings.AWS_STORAGE_BUCKET_NAME != ""

        if self.use_s3:
            # Use actual S3 with environment settings
            self.client = boto3.client(
                "s3",
                settings.AWS_DEFAULT_REGION,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                config=Config(signature_version="s3v4"),
            )
        else:
            # Use local storage
            self.local_storage = LocalS3Storage()

    def get_presigned_url(self, key, time=3600):
        if self.use_s3:
            return self.client.generate_presigned_url(
                ClientMethod="put_object",
                ExpiresIn=time,
                Params={"Bucket": os.environ.get('AWS_STORAGE_BUCKET_NAME', settings.AWS_STORAGE_BUCKET_NAME), "Key": key},
            )
        else:
            return self.local_storage.get_presigned_url(key, time)

    def get_file(self, key, time=604799):
        # If key is empty, return empty string
        if not key:
            return ""

        if self.use_s3:
            try:
                return self.client.generate_presigned_url(
                    ClientMethod="get_object",
                    ExpiresIn=time,
                    Params={"Bucket": os.environ.get('AWS_STORAGE_BUCKET_NAME', settings.AWS_STORAGE_BUCKET_NAME), "Key": key},
                )
            except Exception:
                print("S3 credentials are not set or incorrect")
                return ""
        else:
            return self.local_storage.get_file(key, time)

    def delete_file(self, key):
        if not key:
            return

        if self.use_s3:
            return self.client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key
            )
        else:
            return self.local_storage.delete_file(key)

    def save_file(self, key, content):
        """
        Save a file directly (used for local storage and testing)
        """
        if self.use_s3:
            # For S3, we would normally use the presigned URL from the client side
            # But for direct server-side uploads, we can use put_object
            return self.client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=key,
                Body=content
            )
        else:
            return self.local_storage.save_file(key, content)
