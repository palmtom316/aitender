from pathlib import Path

from app.models.norm_processing_job import NormProcessingJobStatus
from app.services.ocr_dispatcher import OCRDispatcher


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


def test_dispatcher_uses_selected_provider_and_returns_unified_result(tmp_path: Path):
    dispatcher = OCRDispatcher(
        adapters={
            "mineru": FakeSuccessAdapter(),
            "commercial": FakeFailureAdapter(),
        }
    )
    source_file = tmp_path / "norm.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")

    job, result = dispatcher.process_document(
        document_id="doc-1",
        document_path=source_file,
        provider_name="mineru",
    )

    assert job.status == NormProcessingJobStatus.RUNNING
    assert job.provider_name == "mineru"
    assert result == {
        "provider": "mineru",
        "markdown_text": "# Sample",
        "layout_payload": {"pages": [{"page": 1, "text": "Sample"}]},
        "metadata": {"source_path": str(source_file)},
    }


def test_dispatcher_marks_job_failed_when_provider_raises(tmp_path: Path):
    dispatcher = OCRDispatcher(
        adapters={
            "mineru": FakeSuccessAdapter(),
            "commercial": FakeFailureAdapter(),
        }
    )
    source_file = tmp_path / "norm.pdf"
    source_file.write_bytes(b"%PDF-1.7 sample")

    job, result = dispatcher.process_document(
        document_id="doc-2",
        document_path=source_file,
        provider_name="commercial",
    )

    assert job.status == NormProcessingJobStatus.FAILED
    assert job.error_message == "failed to parse norm.pdf"
    assert result is None
