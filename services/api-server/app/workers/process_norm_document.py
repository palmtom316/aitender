from pathlib import Path

from app.services.ocr_dispatcher import OCRDispatcher, ocr_dispatcher


def process_norm_document(
    *,
    document_id: str,
    document_path: Path,
    provider_name: str,
    dispatcher: OCRDispatcher = ocr_dispatcher,
):
    return dispatcher.process_document(
        document_id=document_id,
        document_path=document_path,
        provider_name=provider_name,
    )
