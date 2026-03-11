from pathlib import Path

from app.workers.process_norm_document import process_norm_document


def run_once(document_id: str, document_path: str, provider_name: str):
    return process_norm_document(
        document_id=document_id,
        document_path=Path(document_path),
        provider_name=provider_name,
    )
