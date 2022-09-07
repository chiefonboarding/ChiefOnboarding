import boto3
from botocore.config import Config
from django.conf import settings


class S3:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=Config(signature_version="s3v4"),
        )

    def get_presigned_url(self, key, time=3600):
        return self.client.generate_presigned_url(
            ClientMethod="put_object",
            ExpiresIn=time,
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        )

    def get_file(self, key, time=604799):
        # If a user uploads some files and then removes the keys, this would error
        # Therefore the quick check here
        if settings.AWS_STORAGE_BUCKET_NAME == "":
            return ""

        return self.client.generate_presigned_url(
            ClientMethod="get_object",
            ExpiresIn=time,
            Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
        )

    def delete_file(self, key):
        return self.client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key
        )
