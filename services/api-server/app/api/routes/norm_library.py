from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.dependencies import (
    get_current_user,
    get_document_service,
    get_norm_library_service,
    get_project_service,
)
from app.models.user import AuthenticatedUser
from app.services.document_service import DocumentService
from app.services.norm_library_service import NormLibraryService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects/{project_id}/norm-library", tags=["norm-library"])


def _assert_project_visible(
    *,
    current_user: AuthenticatedUser,
    project_id: str,
    project_service: ProjectService,
) -> None:
    visible_projects = project_service.list_projects_for_user(current_user)
    if project_id not in {project.id for project in visible_projects.items}:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("/documents")
def list_norm_documents(
    project_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: NormLibraryService = Depends(get_norm_library_service),
) -> dict:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    return {"items": service.list_documents(project_id=project_id)}


@router.get("/documents/{document_id}")
def get_norm_document_bundle(
    project_id: str,
    document_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: NormLibraryService = Depends(get_norm_library_service),
) -> dict:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    bundle = service.get_bundle(project_id=project_id, document_id=document_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return bundle


@router.get("/documents/{document_id}/file")
def get_norm_document_file(
    project_id: str,
    document_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    documents: DocumentService = Depends(get_document_service),
) -> FileResponse:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    document = documents.get_document(document_id)
    if document is None or document.project_id != project_id:
        raise HTTPException(status_code=404, detail="Document not found")

    version = documents.get_current_version(document_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Document version not found")

    for artifact in documents.list_artifacts_for_version(version.id):
        if artifact.artifact_type != "original_pdf":
            continue
        artifact_path = Path(artifact.storage_path)
        if not artifact_path.exists():
            break
        return FileResponse(
            path=artifact_path,
            media_type="application/pdf",
            filename=document.file_name,
        )

    raise HTTPException(status_code=404, detail="Original PDF not found")


@router.get("/documents/{document_id}/search")
def search_norm_document(
    project_id: str,
    document_id: str,
    query: str | None = Query(default=None),
    clause_id: str | None = Query(default=None),
    path_prefix: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    project_service: ProjectService = Depends(get_project_service),
    service: NormLibraryService = Depends(get_norm_library_service),
) -> dict:
    _assert_project_visible(
        current_user=current_user,
        project_id=project_id,
        project_service=project_service,
    )
    result = service.search(
        project_id=project_id,
        document_id=document_id,
        query=query,
        clause_id=clause_id,
        path_prefix=path_prefix,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return result
