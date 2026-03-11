from pathlib import Path

from app.services.document_service import DocumentService, document_service
from app.services.ocr_dispatcher import OCRDispatcher, ocr_dispatcher


def process_norm_document(
    *,
    document_id: str,
    document_path: Path,
    provider_name: str,
    dispatcher: OCRDispatcher = ocr_dispatcher,
    documents: DocumentService = document_service,
):
    documents.update_status(document_id, "processing")
    job, result = dispatcher.process_document(
        document_id=document_id,
        document_path=document_path,
        provider_name=provider_name,
    )
    documents.update_status(
        document_id,
        "indexed" if job.status.value == "completed" else "failed",
    )
    return job, result
