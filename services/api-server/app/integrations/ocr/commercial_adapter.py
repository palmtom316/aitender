from pathlib import Path

from app.integrations.ocr.base import OCRAdapter


class CommercialOCRAdapter(OCRAdapter):
    def extract(self, document_path: Path) -> dict:
        raise RuntimeError(
            "Built-in commercial OCR is not configured. Save a project OCR API "
            "endpoint before uploading PDFs for live processing."
        )
