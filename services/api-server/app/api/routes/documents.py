from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.dependencies import (
    get_current_user,
    get_document_service,
    get_project_service,
)
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.models.user import AuthenticatedUser
from app.services.document_service import DocumentService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: DocumentService = Depends(get_document_service),
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
    return {
        "document": document,
        "version": version,
        "artifact": artifact,
    }
