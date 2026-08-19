import os
from urllib.parse import quote

import boto3
from botocore.config import Config
from django.conf import settings


class S3:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            settings.AWS_DEFAULT_REGION,
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

        cdn_url = os.getenv("AWS_CDN_URL", "").strip().rstrip("/")
        if cdn_url:
            return f"{cdn_url}/{quote(key, safe='/')}"

        try:
            return self.client.generate_presigned_url(
                ClientMethod="get_object",
                ExpiresIn=time,
                Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": key},
            )
        except Exception:
            print("Credentials are not set or incorrect")
            return ""

    def put_file(
        self,
        key,
        body,
    ):
        payload = {
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": key,
            "Body": body,
        }

        return self.client.put_object(
            **payload,
        )

    def delete_file(self, key):
        return self.client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key
        )
