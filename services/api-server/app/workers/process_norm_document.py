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
from app.services.norm_ai_scope_patcher import NormAiScopePatcher
from app.services.norm_commentary_builder import NormCommentaryBuilder
from app.services.norm_index_builder import NormIndexBuilder
from app.services.norm_markdown_splitter import NormMarkdownSplitter
from app.services.norm_toc_parser import NormTocParser
from app.services.norm_workflow_validator import NormWorkflowValidator
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
    existing_job_id: str | None = None,
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
        existing_job_id=existing_job_id,
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
                segments = NormMarkdownSplitter().split(normalized.markdown_text)
                toc_expected = NormTocParser().parse_expected_labels(segments.toc_markdown)
                body_page_texts, commentary_page_texts = _slice_page_texts_for_body_and_commentary(
                    page_texts
                )
                baseline_clause_index = NormIndexBuilder().build(
                    document_id=document_id,
                    markdown_text=segments.body_markdown or normalized.markdown_text,
                    page_texts=body_page_texts,
                )
                _populate_content_previews(
                    clause_index=baseline_clause_index,
                    page_texts=body_page_texts,
                )
                baseline_commentary_result = (
                    NormCommentaryBuilder().build(
                        document_id=document_id,
                        markdown_text=segments.commentary_markdown,
                        page_texts=commentary_page_texts,
                    )
                    if segments.commentary_markdown.strip()
                    else {
                        "summary_text": "",
                        "tree": [],
                        "entries": [],
                        "commentary_map": {},
                        "errors": [],
                    }
                )
                clause_labels = {
                    entry["label"]
                    for entry in baseline_clause_index.get("entries", [])
                    if entry.get("node_type") == "clause" and entry.get("label")
                }
                filtered_commentary_map = {
                    label: text
                    for label, text in dict(
                        baseline_commentary_result.get("commentary_map", {})
                    ).items()
                    if label in clause_labels
                }
                baseline_commentary_result["commentary_map"] = filtered_commentary_map
                for entry in baseline_clause_index.get("entries", []):
                    if entry.get("node_type") == "clause":
                        entry["commentary_summary"] = filtered_commentary_map.get(
                            entry.get("label", ""),
                            "",
                        )

                dispatcher.record_step(
                    job_id=job.id,
                    step="clause_index_built",
                    message=(
                        f"Built baseline clause index with "
                        f"{len(baseline_clause_index['entries'])} entries"
                    ),
                )
                dispatcher.record_step(
                    job_id=job.id,
                    step="commentary_built",
                    message=(
                        "Built baseline commentary map with "
                        f"{len(filtered_commentary_map)} clause mappings"
                    ),
                )

                workflow_validation = NormWorkflowValidator().validate(
                    clause_index=baseline_clause_index,
                    commentary_result=baseline_commentary_result,
                    expected_chapters=toc_expected.get("expected_chapters", []),
                    expected_sections=toc_expected.get("expected_sections", []),
                )
                dispatcher.record_step(
                    job_id=job.id,
                    step="rule_validation_completed",
                    message=(
                        "Rule-based validation passed"
                        if workflow_validation["ok"]
                        else "Rule-based validation failed"
                    ),
                    level="info" if workflow_validation["ok"] else "error",
                )

                clause_index = baseline_clause_index
                commentary_result = baseline_commentary_result

                if (
                    not workflow_validation["ok"]
                    and project_settings is not None
                    and project_settings.analysis.is_configured()
                ):
                    dispatcher.record_step(
                        job_id=job.id,
                        step="ai_patch_started",
                        message="Started AI scope patching",
                    )
                    clause_index, commentary_result = NormAiScopePatcher(
                        ai_structurer=ai_structurer
                    ).patch(
                        document_id=document_id,
                        body_markdown=segments.body_markdown or normalized.markdown_text,
                        commentary_markdown=segments.commentary_markdown,
                        body_page_texts=body_page_texts,
                        commentary_page_texts=commentary_page_texts,
                        baseline_clause_index=baseline_clause_index,
                        baseline_commentary_result=baseline_commentary_result,
                        expected_chapters=toc_expected.get("expected_chapters", []),
                        expected_sections=toc_expected.get("expected_sections", []),
                        config=project_settings.analysis,
                    )
                    workflow_validation = NormWorkflowValidator().validate(
                        clause_index=clause_index,
                        commentary_result=commentary_result,
                        expected_chapters=toc_expected.get("expected_chapters", []),
                        expected_sections=toc_expected.get("expected_sections", []),
                    )
                    dispatcher.record_step(
                        job_id=job.id,
                        step="ai_patch_completed",
                        message="AI scope patching completed",
                    )

                if not workflow_validation["ok"]:
                    raise RuntimeError(
                        "Norm parsing failed validation: "
                        + "; ".join(workflow_validation.get("errors", []))
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
                dispatcher.record_step(
                    job_id=job.id,
                    step="structure_persisted",
                    message="Persisted clause/commentary entries",
                )

                debug_artifacts = [
                    ("clause_index_json", "clause_index.json", clause_index),
                    ("commentary_json", "commentary.json", commentary_result),
                    ("validation_json", "validation.json", workflow_validation),
                    (
                        "quality_report_json",
                        "quality_report.json",
                        {
                            "ok": workflow_validation.get("ok", False),
                            "errors": list(workflow_validation.get("errors", [])),
                            "warnings": list(workflow_validation.get("warnings", [])),
                            "stats": dict(workflow_validation.get("stats", {})),
                        },
                    ),
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
                dispatcher.mark_job_status(
                    job,
                    status=NormProcessingJobStatus.COMPLETED,
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


def _slice_page_texts_for_body_and_commentary(
    page_texts: list[dict],
) -> tuple[list[dict], list[dict]]:
    """
    Best-effort正文窗口切分:
    - body starts where we first see "1总则" or "1 总则"
    - commentary starts where we first see "修订说明"
    """
    sorted_pages = sorted(
        [
            {"page": int(item.get("page")), "text": str(item.get("text", ""))}
            for item in page_texts
            if "page" in item
        ],
        key=lambda item: item["page"],
    )
    body_start = None
    revision_start = None
    for item in sorted_pages:
        text = item["text"]
        if body_start is None and ("1总则" in text or "1 总则" in text):
            body_start = item["page"]
        if revision_start is None and "修订说明" in text:
            revision_start = item["page"]

    if sorted_pages and body_start is None:
        body_start = sorted_pages[0]["page"]

    if revision_start is None:
        body_pages = [
            item
            for item in sorted_pages
            if body_start is None or item["page"] >= body_start
        ]
        commentary_pages: list[dict] = []
    else:
        body_pages = [
            item
            for item in sorted_pages
            if body_start is None
            or (item["page"] >= body_start and item["page"] < revision_start)
        ]
        commentary_pages = [
            item for item in sorted_pages if item["page"] >= revision_start
        ]

    return body_pages, commentary_pages


def _populate_content_previews(*, clause_index: dict, page_texts: list[dict]) -> None:
    import re

    page_by_number = {
        int(item.get("page")): str(item.get("text", ""))
        for item in page_texts
        if "page" in item
    }
    next_label_pattern = re.compile(r"\d+(?:\.\d+)+")

    for entry in clause_index.get("entries", []):
        if entry.get("node_type") != "clause":
            continue
        if entry.get("content_preview"):
            continue

        label = str(entry.get("label", "")).strip()
        page_start = entry.get("page_start")
        if not label or not isinstance(page_start, int):
            continue

        text = page_by_number.get(page_start, "")
        if not text:
            continue

        idx = text.find(label)
        if idx == -1:
            entry["content_preview"] = label
            continue

        end = min(len(text), idx + 800)
        for match in next_label_pattern.finditer(text, idx + len(label)):
            next_label = match.group(0)
            if next_label != label:
                end = match.start()
                break

        window = text[idx:end].strip()
        if len(window) > 320:
            window = window[:320].rstrip()
        entry["content_preview"] = window
