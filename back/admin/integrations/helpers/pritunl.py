import base64
import hashlib
import hmac
import time
import uuid
from urllib.parse import urlsplit

from admin.integrations.exceptions import PritunlMissingCredentialsError


def pritunl_headers(method, url, extra_args):
    api_token = extra_args.get("API_TOKEN") or extra_args.get("PRITUNL_API_TOKEN")
    api_secret = extra_args.get("API_SECRET") or extra_args.get("PRITUNL_API_SECRET")

    if not api_token or not api_secret:
        raise PritunlMissingCredentialsError(
            "Missing API_TOKEN/API_SECRET (or legacy PRITUNL_API_* keys)"
        )

    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex

    parsed = urlsplit(url)
    request_path = parsed.path + (f"?{parsed.query}" if parsed.query else "")

    auth_string = "&".join(
        [
            api_token,
            auth_timestamp,
            auth_nonce,
            method.upper(),
            request_path,
        ]
    )

    auth_signature = base64.b64encode(
        hmac.new(
            api_secret.encode("utf-8"),
            auth_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    return {
        "Auth-Token": api_token,
        "Auth-Timestamp": auth_timestamp,
        "Auth-Nonce": auth_nonce,
        "Auth-Signature": auth_signature,
    }
