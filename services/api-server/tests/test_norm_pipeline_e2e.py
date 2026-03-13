from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit_service import audit_service
from app.services.document_service import document_service
from app.services.ocr_dispatcher import ocr_dispatcher
from app.workers.process_norm_document import process_norm_document


class FakeSuccessAdapter:
    def extract(self, document_path: Path):
        return {
            "provider": "mineru",
            "markdown_text": (
                "# 1 General\n"
                "1.0.1 General clause text for the project.\n\n"
                "## 1.1 Scope\n"
                "1.1.1 Scope clause text that explains the implementation scope.\n"
            ),
            "layout_payload": {
                "pages": [
                    {
                        "page": 1,
                        "text": (
                            "1 General 1.0.1 General clause text for the project. "
                            "1.1 Scope 1.1.1 Scope clause text that explains the "
                            "implementation scope."
                        ),
                    }
                ]
            },
            "metadata": {"source_path": str(document_path)},
        }


@pytest.fixture(autouse=True)
def reset_pipeline_state():
    document_service.reset()
    audit_service.reset()
    ocr_dispatcher.reset(adapters={"mineru": FakeSuccessAdapter()})
    yield
    document_service.reset()
    audit_service.reset()
    ocr_dispatcher.reset(adapters={"mineru": FakeSuccessAdapter()})


def test_norm_pipeline_e2e_from_upload_to_searchable_result():
    client = TestClient(app)

    upload = client.post(
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

    assert upload.status_code == 201
    payload = upload.json()
    document_id = payload["document"]["id"]
    artifact_path = Path(payload["artifact"]["storage_path"])

    job, raw_result = process_norm_document(
        document_id=document_id,
        document_path=artifact_path,
        provider_name="mineru",
    )
    assert raw_result is not None

    search = client.post(
        "/norm-search/query",
        json={
            "document_id": document_id,
            "query": "implementation scope",
        },
    )

    assert search.status_code == 200
    assert search.json()["items"] == [
        {
            "label": "1.1.1",
            "title": "Scope clause text that explains the implementation scope.",
            "page_start": 1,
            "page_end": 1,
            "summary_text": "Scope clause text that explains the implementation scope.",
            "commentary_summary": "",
            "path_labels": ["1", "1.1", "1.1.1"],
            "tags": [],
        }
    ]

    status = client.get(f"/jobs/{job.id}")
    assert status.status_code == 200
    assert status.json()["job"]["status"] == "completed"
    assert document_service.get_document(document_id).status == "indexed"
