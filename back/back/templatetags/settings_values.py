# Source: https://stackoverflow.com/a/7716141
import boto3

from django import template
from django.core.cache import cache
from django.conf import settings
from botocore.config import Config

register = template.Library()


@register.simple_tag
def aws_enabled():
    # Early return if credentials are not set at all
    if settings.AWS_STORAGE_BUCKET_NAME == "":
        return False

    if cache.get("aws_checked"):
        return True

    # Try if we can make a connection
    try:
        boto3.client(
            "s3",
            settings.AWS_REGION,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            config=Config(signature_version="s3v4"),
        ).head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        cache.set("aws_checked", True, timeout=None)
        return True
    except Exception:
        return False


@register.simple_tag
def text_enabled():
    return settings.TWILIO_FROM_NUMBER != ""
