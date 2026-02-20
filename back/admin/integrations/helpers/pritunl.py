import base64
import codecs
import hashlib
import hmac
import time
import uuid


def pritunl_headers(method, path, extra_args):
    auth_timestamp = str(int(time.time()))
    auth_nonce = uuid.uuid4().hex
    auth_string = "&".join(
        [extra_args["API_TOKEN"], auth_timestamp, auth_nonce, method.upper(), path]
    )
    auth_signature = base64.b64encode(
        hmac.new(
            codecs.encode(extra_args["API_SECRET"]),
            codecs.encode(auth_string),
            hashlib.sha256,
        ).digest()
    )
    auth_headers = {
        "Auth-Token": extra_args["API_TOKEN"],
        "Auth-Timestamp": auth_timestamp,
        "Auth-Nonce": auth_nonce,
        "Auth-Signature": auth_signature.decode("utf-8"),
    }
    return auth_headers
