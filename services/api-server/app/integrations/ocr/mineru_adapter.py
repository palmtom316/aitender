from pathlib import Path

from app.integrations.ocr.base import OCRAdapter


class MineruOCRAdapter(OCRAdapter):
    def extract(self, document_path: Path) -> dict:
        return {
            "provider": "mineru",
            "markdown_text": "",
            "layout_payload": {"pages": []},
            "metadata": {"source_path": str(document_path)},
        }
