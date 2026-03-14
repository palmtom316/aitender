from pathlib import Path
from zipfile import ZipFile

import json

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


def test_remote_ocr_service_supports_mineru_async_batch_flow(tmp_path: Path):
    source = tmp_path / "grid-standard.pdf"
    source.write_bytes(b"%PDF-1.7 sample")
    zip_path = tmp_path / "mineru-result.zip"
    with ZipFile(zip_path, "w") as archive:
        archive.writestr("result/full.md", "# 1 General\n1.0.1 Clause text")
        archive.writestr(
            "result/layout.json",
            json.dumps(
                {
                    "pdf_info": [
                        {
                            "page_no": 1,
                            "para_blocks": [
                                {"text": "1 General"},
                                {"text": "1.0.1 Clause text"},
                            ],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
        )

    class AsyncMineruRemoteOCRService(RemoteOCRService):
        def __init__(self) -> None:
            self.post_calls: list[dict] = []
            self.put_calls: list[dict] = []
            self.poll_calls: list[dict] = []
            self.download_calls: list[dict] = []

        def _post_json(self, **kwargs) -> dict:
            self.post_calls.append(kwargs)
            return {
                "batch_id": "batch-1",
                "file_urls": [
                    {
                        "name": source.name,
                        "url": "https://upload.example.test/file-1",
                    }
                ],
            }

        def _put_bytes(self, **kwargs) -> None:
            self.put_calls.append(kwargs)

        def _poll_mineru_batch_result(self, **kwargs) -> dict:
            self.poll_calls.append(kwargs)
            return {
                "extract_result": [
                    {
                        "file_name": source.name,
                        "state": "done",
                        "full_zip_url": "https://download.example.test/result.zip",
                    }
                ]
            }

        def _download_bytes(self, **kwargs) -> bytes:
            self.download_calls.append(kwargs)
            return zip_path.read_bytes()

    service = AsyncMineruRemoteOCRService()

    result = service.extract(
        document_path=source,
        config=ProviderApiConfig(
            base_url="https://mineru.net/api/v4/extract/task",
            api_key="secret",
            model="vlm",
        ),
    )

    assert service.post_calls[0]["url"] == "https://mineru.net/api/v4/file-urls/batch"
    assert service.put_calls[0]["url"] == "https://upload.example.test/file-1"
    assert service.poll_calls[0]["batch_id"] == "batch-1"
    assert service.download_calls[0]["url"] == "https://download.example.test/result.zip"
    assert result["provider"] == "mineru"
    assert result["markdown_text"].startswith("# 1 General")
    assert result["layout_payload"]["pages"] == [{"page": 1, "text": "1 General 1.0.1 Clause text"}]
    assert result["metadata"]["source_path"] == str(source)
    assert result["metadata"]["provider_batch_id"] == "batch-1"
