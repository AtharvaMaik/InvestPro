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


def test_auth_login_and_me_endpoint():
    login = client.post("/auth/login", json={"email": "investor@example.com", "name": "Investor"})
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "investor@example.com"
