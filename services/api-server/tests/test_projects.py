from fastapi.testclient import TestClient

from app.main import app


def test_projects_endpoint_returns_only_projects_visible_to_writer():
    client = TestClient(app)

    response = client.get(
        "/projects",
        headers={"Authorization": "Bearer auth-token-writer"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "project-alpha",
                "organization_id": "org-1",
                "name": "Alpha Substation Bid",
                "member_role": "writer",
            }
        ]
    }


def test_projects_endpoint_requires_authentication():
    client = TestClient(app)

    response = client.get("/projects")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing bearer token"}


def test_projects_endpoint_rejects_forged_predictable_token():
    client = TestClient(app)

    response = client.get(
        "/projects",
        headers={"Authorization": "Bearer token-user-admin"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid bearer token"}
