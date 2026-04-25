from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from functools import lru_cache
from pathlib import Path


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
    configured = os.getenv("INVESTPRO_SESSION_SECRET")
    if configured:
        return configured.encode("utf-8")
    return _persistent_fallback_secret()


@lru_cache(maxsize=1)
def _persistent_fallback_secret() -> bytes:
    secret_file = Path(os.getenv("INVESTPRO_SESSION_SECRET_FILE", _default_secret_file()))
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    if secret_file.exists():
        stored = secret_file.read_text(encoding="utf-8").strip()
        if stored:
            return stored.encode("utf-8")

    generated = secrets.token_urlsafe(32)
    secret_file.write_text(generated, encoding="utf-8")
    return generated.encode("utf-8")


def _default_secret_file() -> str:
    return str(Path(__file__).resolve().parents[2] / ".investpro-session-secret")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode("ascii")
