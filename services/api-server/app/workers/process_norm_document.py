from pathlib import Path

from app.core.config import settings
from app.models.norm_processing_job import NormProcessingJobStatus
from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.factory import get_norm_structure_repository
from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.document_service import DocumentService, document_service
from app.services.norm_ai_structurer import NormAIStructurer, norm_ai_structurer
from app.services.norm_artifact_normalizer import NormArtifactNormalizer
from app.services.norm_artifact_store import NormArtifactStore
from app.services.norm_index_builder import NormIndexBuilder
from app.services.norm_structure_validator import NormStructureValidator
from app.services.ocr_dispatcher import OCRDispatcher, ocr_dispatcher
from app.services.project_ai_settings_service import (
    ProjectAiSettingsService,
    project_ai_settings_service,
)
from app.services.remote_ocr_service import RemoteOCRService, remote_ocr_service


def process_norm_document(
    *,
    document_id: str,
    document_path: Path,
    provider_name: str,
    dispatcher: OCRDispatcher = ocr_dispatcher,
    documents: DocumentService = document_service,
    structure_repository: NormStructureRepository | None = None,
    ai_settings: ProjectAiSettingsService = project_ai_settings_service,
    remote_ocr: RemoteOCRService = remote_ocr_service,
    ai_structurer: NormAIStructurer = norm_ai_structurer,
):
    structure_repository = structure_repository or get_norm_structure_repository()
    documents.update_status(document_id, "processing")
    document = documents.get_document(document_id)
    project_id = document.project_id if document is not None else None
    project_settings = (
        ai_settings.get_settings(project_id) if project_id is not None else None
    )
    extract_override = None
    runtime_provider_name = provider_name
    if project_settings is not None and project_settings.ocr.is_configured():
        runtime_provider_name = "configured-ocr"
        extract_override = lambda path: remote_ocr.extract(
            document_path=path,
            config=project_settings.ocr,
        )

    job, result = dispatcher.process_document(
        document_id=document_id,
        document_path=document_path,
        provider_name=runtime_provider_name,
        extract_override=extract_override,
    )
    documents.update_latest_job(document_id, job.id)

    if result is not None:
        try:
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
                baseline_clause_index = NormIndexBuilder().build(
                    document_id=document_id,
                    markdown_text=normalized.markdown_text,
                    page_texts=page_texts,
                )
                dispatcher.record_step(
                    job_id=job.id,
                    step="clause_index_built",
                    message=(
                        f"Built baseline clause index with "
                        f"{len(baseline_clause_index['entries'])} entries"
                    ),
                )

                if (
                    project_settings is not None
                    and project_settings.analysis.is_configured()
                ):
                    dispatcher.record_step(
                        job_id=job.id,
                        step="ai_structure_started",
                        message="Started AI structure generation",
                    )
                    clause_index, commentary_result = ai_structurer.generate(
                        document_id=document_id,
                        markdown_text=normalized.markdown_text,
                        page_texts=page_texts,
                        baseline_clause_index=baseline_clause_index,
                        config=project_settings.analysis,
                    )
                    dispatcher.record_step(
                        job_id=job.id,
                        step="ai_structure_completed",
                        message="AI structure generation completed",
                    )
                else:
                    clause_index = baseline_clause_index
                    commentary_result = {
                        "summary_text": "",
                        "tree": [],
                        "entries": [],
                        "commentary_map": {},
                        "errors": [],
                    }
                    dispatcher.record_step(
                        job_id=job.id,
                        step="ai_structure_skipped",
                        message=(
                            "AI analysis settings are empty; persisted baseline "
                            "clause index without AI enrichment"
                        ),
                    )

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
                dispatcher.record_step(
                    job_id=job.id,
                    step="structure_validated",
                    message=(
                        "Structure validation passed"
                        if validation_result["ok"]
                        else "Structure validation reported errors"
                    ),
                    level="info" if validation_result["ok"] else "error",
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
        except Exception as exc:
            dispatcher.mark_job_status(
                job,
                status=NormProcessingJobStatus.FAILED,
                error_message=str(exc),
            )
            dispatcher.record_step(
                job_id=job.id,
                step="structure_failed",
                message=str(exc),
                level="error",
            )

    documents.update_status(
        document_id,
        "indexed" if job.status.value == "completed" else "failed",
    )
    return job, result
