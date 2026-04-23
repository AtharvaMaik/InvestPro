from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


SESSION_TTL_SECONDS = 60 * 60 * 24 * 14


def create_session_token(email: str, name: str) -> str:
    payload = {
        "email": email.strip().lower(),
        "name": name.strip() or email.strip().split("@")[0],
        "iat": int(time.time()),
        "exp": int(time.time()) + SESSION_TTL_SECONDS,
    }
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = _sign(body)
    return f"{body}.{signature}"


def verify_session_token(token: str) -> dict | None:
    try:
        body, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(body), signature):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(_pad(body)).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    if not payload.get("email"):
        return None
    return payload


def _sign(body: str) -> str:
    return _b64(hmac.new(_secret(), body.encode("utf-8"), hashlib.sha256).digest())


def _secret() -> bytes:
    return os.getenv("INVESTPRO_SESSION_SECRET", "investpro-development-session-secret").encode("utf-8")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode("ascii")
