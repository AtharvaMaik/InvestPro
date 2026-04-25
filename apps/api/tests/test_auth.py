import importlib

from app.core.auth import create_session_token, verify_session_token
from app.main import app
from fastapi.testclient import TestClient


client = TestClient(app)


def test_session_token_roundtrip():
    token = create_session_token("investor@example.com", "Investor")
    user = verify_session_token(token)

    assert user["email"] == "investor@example.com"
    assert user["name"] == "Investor"


def test_session_token_rejects_tampering():
    token = create_session_token("investor@example.com", "Investor")
    tampered = token[:-2] + "xx"

    assert verify_session_token(tampered) is None


def test_session_token_does_not_use_public_default_secret(monkeypatch):
    import app.core.auth as auth_module

    monkeypatch.delenv("INVESTPRO_SESSION_SECRET", raising=False)
    reloaded = importlib.reload(auth_module)
    monkeypatch.setattr(reloaded.time, "time", lambda: 1_700_000_000)

    token = reloaded.create_session_token("investor@example.com", "Investor")

    assert token != "eyJlbWFpbCI6ImludmVzdG9yQGV4YW1wbGUuY29tIiwiZXhwIjoxNzAxMjA5NjAwLCJpYXQiOjE3MDAwMDAwMDAsIm5hbWUiOiJJbnZlc3RvciJ9.HglVH_hsTEiNo2y73mAxaghFpaBvbvqki-e4GX7JORs"


def test_session_token_persists_across_reload_with_file_backed_fallback(monkeypatch, tmp_path):
    import app.core.auth as auth_module

    secret_file = tmp_path / "session-secret.txt"
    monkeypatch.delenv("INVESTPRO_SESSION_SECRET", raising=False)
    monkeypatch.setenv("INVESTPRO_SESSION_SECRET_FILE", str(secret_file))

    first_module = importlib.reload(auth_module)
    monkeypatch.setattr(first_module.time, "time", lambda: 1_700_000_000)
    token = first_module.create_session_token("investor@example.com", "Investor")

    second_module = importlib.reload(first_module)
    monkeypatch.setattr(second_module.time, "time", lambda: 1_700_000_000)

    assert secret_file.exists()
    assert second_module.verify_session_token(token)["email"] == "investor@example.com"


def test_auth_login_and_me_endpoint():
    login = client.post("/auth/login", json={"email": "investor@example.com", "name": "Investor"})
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "investor@example.com"
