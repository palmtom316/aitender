from fastapi.testclient import TestClient

from app.main import app


def test_login_returns_token_for_valid_credentials():
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "pm@aitender.local", "password": "pm-pass"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "auth-token-pm",
        "token_type": "bearer",
        "user": {
            "id": "user-pm",
            "organization_id": "org-1",
            "role": "project_manager",
            "display_name": "Project Manager",
        },
    }


def test_login_rejects_invalid_credentials():
    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={"email": "pm@aitender.local", "password": "wrong-pass"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
