from pathlib import Path

from app.integrations.ocr.base import OCRAdapter


class CommercialOCRAdapter(OCRAdapter):
    def extract(self, document_path: Path) -> dict:
        return {
            "provider": "commercial",
            "markdown_text": "",
            "layout_payload": {"pages": []},
            "metadata": {"source_path": str(document_path)},
        }
