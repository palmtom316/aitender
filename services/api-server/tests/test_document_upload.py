from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_service import document_service


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
