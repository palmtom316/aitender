from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.audit_service import audit_service
from app.services.ocr_dispatcher import OCRDispatcher, ocr_dispatcher


class FakeSuccessAdapter:
    def extract(self, document_path: Path):
        return {
            "provider": "mineru",
            "markdown_text": "# Sample",
            "layout_payload": {"pages": [{"page": 1, "text": "Sample"}]},
            "metadata": {"source_path": str(document_path)},
        }


class FakeFailureAdapter:
    def extract(self, document_path: Path):
        raise RuntimeError(f"failed to parse {document_path.name}")


@pytest.fixture(autouse=True)
def reset_processing_services():
    ocr_dispatcher.reset(
        adapters={
            "mineru": FakeSuccessAdapter(),
            "commercial": FakeFailureAdapter(),
        }
    )
    audit_service.reset()
    yield
    ocr_dispatcher.reset(
        adapters={
            "mineru": FakeSuccessAdapter(),
            "commercial": FakeFailureAdapter(),
        }
    )
    audit_service.reset()


def test_job_status_endpoint_returns_completed_job_and_audit_logs(tmp_path: Path):
    source_file = tmp_path / "norm.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")
    job, _ = ocr_dispatcher.process_document(
        document_id="doc-1",
        document_path=source_file,
        provider_name="mineru",
    )
    client = TestClient(app)

    response = client.get(f"/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json() == {
        "job": {
            "id": job.id,
            "document_id": "doc-1",
            "provider_name": "mineru",
            "status": "completed",
            "error_message": None,
        },
        "audit_logs": [
            {
                "job_id": job.id,
                "step": "job_started",
                "message": "Started OCR processing with mineru",
                "level": "info",
            },
            {
                "job_id": job.id,
                "step": "ocr_completed",
                "message": "OCR processing completed",
                "level": "info",
            },
        ],
    }


def test_job_status_endpoint_returns_failure_reason_and_error_log(tmp_path: Path):
    source_file = tmp_path / "broken.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")
    job, _ = ocr_dispatcher.process_document(
        document_id="doc-2",
        document_path=source_file,
        provider_name="commercial",
    )
    client = TestClient(app)

    response = client.get(f"/jobs/{job.id}")

    assert response.status_code == 200
    assert response.json()["job"] == {
        "id": job.id,
        "document_id": "doc-2",
        "provider_name": "commercial",
        "status": "failed",
        "error_message": "failed to parse broken.pdf",
    }
    assert response.json()["audit_logs"][-1] == {
        "job_id": job.id,
        "step": "ocr_failed",
        "message": "failed to parse broken.pdf",
        "level": "error",
    }


def test_unknown_provider_transitions_job_to_failed_and_records_audit(tmp_path: Path):
    source_file = tmp_path / "unknown-provider.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")

    job, result = ocr_dispatcher.process_document(
        document_id="doc-3",
        document_path=source_file,
        provider_name="unknown-provider",
    )
    client = TestClient(app)

    response = client.get(f"/jobs/{job.id}")

    assert result is None
    assert response.status_code == 200
    assert response.json()["job"] == {
        "id": job.id,
        "document_id": "doc-3",
        "provider_name": "unknown-provider",
        "status": "failed",
        "error_message": "Unsupported OCR provider: unknown-provider",
    }
    assert response.json()["audit_logs"][-1] == {
        "job_id": job.id,
        "step": "ocr_failed",
        "message": "Unsupported OCR provider: unknown-provider",
        "level": "error",
    }
