from pathlib import Path

from app.integrations.ocr.base import OCRAdapter


class MineruOCRAdapter(OCRAdapter):
    def extract(self, document_path: Path) -> dict:
        raise RuntimeError(
            "Built-in MinerU OCR is not configured. Save a project OCR API "
            "endpoint before uploading PDFs for live processing."
        )
