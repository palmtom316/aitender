from fastapi.testclient import TestClient

from app.api.dependencies import get_project_ai_settings_service
from app.main import app
from app.services.project_ai_settings_service import ProjectAiSettingsService


def test_project_ai_settings_route_reads_and_writes_project_config(tmp_path):
    service = ProjectAiSettingsService(state_path=tmp_path / "project-ai-settings.json")
    client = TestClient(app)
    app.dependency_overrides[get_project_ai_settings_service] = lambda: service

    try:
        response = client.get(
            "/projects/project-alpha/settings/ai",
            headers={"Authorization": "Bearer auth-token-pm"},
        )

        assert response.status_code == 200
        assert response.json() == {
            "project_id": "project-alpha",
            "ocr": {"base_url": "", "api_key": "", "model": ""},
            "analysis": {"base_url": "", "api_key": "", "model": ""},
        }

        update = client.put(
            "/projects/project-alpha/settings/ai",
            headers={"Authorization": "Bearer auth-token-pm"},
            json={
                "project_id": "project-alpha",
                "ocr": {
                    "base_url": "https://ocr.example.test/extract",
                    "api_key": "ocr-secret",
                    "model": "mineru-remote",
                },
                "analysis": {
                    "base_url": "https://ai.example.test/v1",
                    "api_key": "ai-secret",
                    "model": "deepseek-chat",
                },
            },
        )

        assert update.status_code == 200
        assert update.json()["ocr"]["model"] == "mineru-remote"
        assert update.json()["analysis"]["model"] == "deepseek-chat"
    finally:
        app.dependency_overrides.clear()


def test_project_ai_settings_route_accepts_cors_preflight(tmp_path):
    service = ProjectAiSettingsService(state_path=tmp_path / "project-ai-settings.json")
    client = TestClient(app)
    app.dependency_overrides[get_project_ai_settings_service] = lambda: service

    try:
        response = client.options(
            "/projects/project-alpha/settings/ai",
            headers={
                "Origin": "http://localhost:3011",
                "Access-Control-Request-Method": "PUT",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3011"
    finally:
        app.dependency_overrides.clear()
