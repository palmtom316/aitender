from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_ocr_dispatcher
from app.main import app
from app.services.document_service import document_service
from app.services.ocr_dispatcher import OCRDispatcher


@pytest.fixture(autouse=True)
def reset_document_service_state():
    document_service.reset()
    yield
    document_service.reset()


def test_upload_norm_pdf_creates_document_version_and_artifact():
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        headers={"Authorization": "Bearer auth-token-pm"},
        data={"project_id": "project-alpha"},
        files={
            "file": (
                "grid-standard.pdf",
                BytesIO(b"%PDF-1.7 sample"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["document"]["project_id"] == "project-alpha"
    assert payload["document"]["library_type"] == "norm_library"
    assert payload["document"]["status"] == "processing"
    assert payload["document"]["latest_job_id"].startswith("norm-job-")
    assert payload["version"]["version_number"] == 1
    assert payload["artifact"]["artifact_type"] == "original_pdf"
    assert payload["artifact"]["storage_path"].endswith("grid-standard.pdf")


def test_upload_rejects_non_pdf_without_creating_dirty_records():
    client = TestClient(app)

    response = client.post(
        "/documents/upload",
        headers={"Authorization": "Bearer auth-token-pm"},
        data={"project_id": "project-alpha"},
        files={
            "file": (
                "notes.txt",
                BytesIO(b"plain text"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Only PDF uploads are supported in Phase 1"}
    assert document_service.document_count() == 0


def test_upload_route_accepts_cors_preflight():
    client = TestClient(app)

    response = client.options(
        "/documents/upload",
        headers={
            "Origin": "http://localhost:3011",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3011"


def test_upload_schedules_background_processing_without_waiting(tmp_path, monkeypatch):
    dispatcher = OCRDispatcher(state_path=tmp_path / "jobs.json")
    scheduled: dict = {}
    client = TestClient(app)
    app.dependency_overrides[get_ocr_dispatcher] = lambda: dispatcher

    def fake_start_norm_processing(**kwargs):
        scheduled.update(kwargs)
        return None

    monkeypatch.setattr("app.api.routes.documents._start_norm_processing", fake_start_norm_processing)

    try:
        response = client.post(
            "/documents/upload",
            headers={"Authorization": "Bearer auth-token-pm"},
            data={"project_id": "project-alpha"},
            files={
                "file": (
                    "grid-standard.pdf",
                    BytesIO(b"%PDF-1.7 sample"),
                    "application/pdf",
                )
            },
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["document"]["status"] == "processing"
        assert payload["document"]["latest_job_id"] == scheduled["existing_job_id"]
        assert scheduled["document_id"] == payload["document"]["id"]
        assert dispatcher.get_job(scheduled["existing_job_id"]) is not None
    finally:
        app.dependency_overrides.clear()
