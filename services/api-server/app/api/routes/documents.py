from pathlib import Path
from threading import Thread
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies import (
    get_current_user,
    get_document_service,
    get_ocr_dispatcher,
    get_project_service,
)
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.models.norm_processing_job import NormProcessingJobStatus
from app.models.user import AuthenticatedUser
from app.services.document_service import DocumentService
from app.services.ocr_dispatcher import OCRDispatcher
from app.services.project_service import ProjectService
from app.workers.process_norm_document import process_norm_document

router = APIRouter(prefix="/documents", tags=["documents"])


def _start_norm_processing(**kwargs) -> Thread:
    thread = Thread(target=process_norm_document, kwargs=kwargs, daemon=True)
    thread.start()
    return thread


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    provider_name: Annotated[str, Form()] = "mineru",
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: DocumentService = Depends(get_document_service),
    dispatcher: OCRDispatcher = Depends(get_ocr_dispatcher),
) -> dict[str, Document | DocumentVersion | DocumentArtifact]:
    visible_projects = project_service.list_projects_for_user(current_user)
    if project_id not in {project.id for project in visible_projects.items}:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Project not found")

    payload = await file.read()
    document, version, artifact = service.create_upload(
        current_user=current_user,
        project_id=project_id,
        filename=file.filename or "upload.pdf",
        content_type=file.content_type or "",
        content=payload,
    )
    job = dispatcher.create_job(
        document_id=document.id,
        provider_name=provider_name,
        status=NormProcessingJobStatus.PENDING,
    )
    service.update_status(document.id, "processing")
    service.update_latest_job(document.id, job.id)
    _start_norm_processing(
        document_id=document.id,
        document_path=Path(artifact.storage_path),
        provider_name=provider_name,
        existing_job_id=job.id,
        documents=service,
        dispatcher=dispatcher,
    )
    refreshed_document = service.get_document(document.id) or document
    refreshed_version = service.get_current_version(document.id) or version
    refreshed_artifact = artifact
    for candidate in service.list_artifacts_for_version(refreshed_version.id):
        if candidate.artifact_type == "original_pdf":
            refreshed_artifact = candidate
            break

    return {
        "document": refreshed_document,
        "version": refreshed_version,
        "artifact": refreshed_artifact,
    }
