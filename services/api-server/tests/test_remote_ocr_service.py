from pathlib import Path

from app.models.project_ai_settings import ProviderApiConfig
from app.services.remote_ocr_service import RemoteOCRService


class FakeRemoteOCRService(RemoteOCRService):
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def _post_multipart(self, **kwargs) -> dict:
        return self.payload


def test_remote_ocr_service_accepts_normalized_response(tmp_path: Path):
    source = tmp_path / "grid-standard.pdf"
    source.write_bytes(b"%PDF-1.7 sample")
    service = FakeRemoteOCRService(
        {
            "provider": "mineru",
            "markdown_text": "# 1 General\n1.0.1 Clause text",
            "layout_payload": {"pages": [{"page": 1, "text": "Clause text"}]},
            "metadata": {"provider_job_id": "ocr-1"},
        }
    )

    result = service.extract(
        document_path=source,
        config=ProviderApiConfig(
            base_url="https://ocr.example.test/extract",
            api_key="secret",
            model="mineru",
        ),
    )

    assert result["provider"] == "mineru"
    assert result["layout_payload"]["pages"][0]["page"] == 1
    assert result["metadata"]["source_path"] == str(source)


def test_remote_ocr_service_accepts_wrapped_commercial_response(tmp_path: Path):
    source = tmp_path / "grid-standard.pdf"
    source.write_bytes(b"%PDF-1.7 sample")
    service = FakeRemoteOCRService(
        {
            "data": {
                "markdown": "# 1 General\n1.0.1 Clause text",
                "pages": [{"page_number": 1, "content": "Clause text"}],
                "meta": {"provider_job_id": "ocr-2"},
            }
        }
    )

    result = service.extract(
        document_path=source,
        config=ProviderApiConfig(
            base_url="https://ocr.example.test/extract",
            api_key="secret",
            model="commercial-ocr",
        ),
    )

    assert result["provider"] == "commercial"
    assert result["pages"][0]["page_number"] == 1
    assert result["meta"]["source_path"] == str(source)
