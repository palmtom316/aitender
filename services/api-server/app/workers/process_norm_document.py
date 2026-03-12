from pathlib import Path

from app.core.config import settings
from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.factory import get_norm_structure_repository
from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.document_service import DocumentService, document_service
from app.services.norm_artifact_normalizer import NormArtifactNormalizer
from app.services.norm_artifact_store import NormArtifactStore
from app.services.norm_index_builder import NormIndexBuilder
from app.services.norm_structure_validator import NormStructureValidator
from app.services.ocr_dispatcher import OCRDispatcher, ocr_dispatcher


def process_norm_document(
    *,
    document_id: str,
    document_path: Path,
    provider_name: str,
    dispatcher: OCRDispatcher = ocr_dispatcher,
    documents: DocumentService = document_service,
    structure_repository: NormStructureRepository | None = None,
):
    structure_repository = structure_repository or get_norm_structure_repository()
    documents.update_status(document_id, "processing")
    job, result = dispatcher.process_document(
        document_id=document_id,
        document_path=document_path,
        provider_name=provider_name,
    )
    documents.update_latest_job(document_id, job.id)

    if result is not None:
        version = documents.get_current_version(document_id)
        if version is not None:
            normalized = NormArtifactNormalizer().normalize(result)
            store = NormArtifactStore(settings.storage_root / "norm_artifacts")
            stored = store.save(
                document_id=document_id,
                version_id=version.id,
                artifacts=normalized,
            )
            documents.add_artifact(
                document_version_id=version.id,
                artifact_type="normalized_markdown",
                storage_path=str(stored.markdown_path),
            )
            documents.add_artifact(
                document_version_id=version.id,
                artifact_type="normalized_layout_json",
                storage_path=str(stored.layout_json_path),
            )
            documents.add_artifact(
                document_version_id=version.id,
                artifact_type="normalized_metadata_json",
                storage_path=str(stored.metadata_json_path),
            )

            page_texts = [page.model_dump() for page in normalized.page_texts]
            clause_index = NormIndexBuilder().build(
                document_id=document_id,
                markdown_text=normalized.markdown_text,
                page_texts=page_texts,
            )
            commentary_result = {
                "entries": [],
                "commentary_map": {},
                "errors": [],
            }
            structure_repository.replace_clause_entries(
                document_id,
                [
                    NormClauseEntry.model_validate(entry)
                    for entry in clause_index["entries"]
                ],
            )
            structure_repository.replace_commentary_entries(
                document_id,
                [
                    NormCommentaryEntry.model_validate(entry)
                    for entry in commentary_result["entries"]
                ],
            )
            validation_result = NormStructureValidator().validate(
                clause_index=clause_index,
                commentary_result=commentary_result,
            )

            debug_artifacts = [
                ("validation_json", "validation.json", validation_result),
            ]
            if not structure_repository.supports_persisted_search():
                debug_artifacts = [
                    ("clause_index_json", "clause_index.json", clause_index),
                    ("commentary_json", "commentary.json", commentary_result),
                    *debug_artifacts,
                ]

            for artifact_type, filename, payload in debug_artifacts:
                target_path = store.save_json(
                    document_id=document_id,
                    version_id=version.id,
                    filename=filename,
                    payload=payload,
                )
                documents.add_artifact(
                    document_version_id=version.id,
                    artifact_type=artifact_type,
                    storage_path=str(target_path),
                )

    documents.update_status(
        document_id,
        "indexed" if job.status.value == "completed" else "failed",
    )
    return job, result
