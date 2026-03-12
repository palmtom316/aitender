from pathlib import Path

from fastapi import HTTPException, status

from app.integrations.storage.local import LocalObjectStorage
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.models.user import AuthenticatedUser
from app.repositories.factory import get_document_repository
from app.repositories.document_repository import DocumentRepository
from app.repositories.json_document_repository import JsonDocumentRepository
from app.core.config import settings


class DocumentService:
    def __init__(
        self,
        *,
        state_path: Path | None = None,
        storage_root: Path | None = None,
        repository: DocumentRepository | None = None,
    ) -> None:
        self._repository = (
            repository
            or JsonDocumentRepository(state_path=state_path)
            if state_path is not None
            else get_document_repository()
        )
        self._storage = LocalObjectStorage(
            storage_root or settings.storage_root,
        )

    def reset(self) -> None:
        self._repository.reset()
        self._storage.reset()

    def document_count(self) -> int:
        return len(self._repository.list_documents())

    def list_documents(
        self,
        *,
        project_id: str | None = None,
        library_type: str | None = None,
    ) -> list[Document]:
        items = self._repository.list_documents()
        if project_id is not None:
            items = [
                document for document in items if document.project_id == project_id
            ]
        if library_type is not None:
            items = [
                document for document in items if document.library_type == library_type
            ]
        return items

    def get_document(self, document_id: str) -> Document | None:
        return self._repository.get_document(document_id)

    def get_current_version(self, document_id: str) -> DocumentVersion | None:
        return self._repository.get_current_version(document_id)

    def list_artifacts_for_version(
        self,
        document_version_id: str,
    ) -> list[DocumentArtifact]:
        return self._repository.list_artifacts_for_version(document_version_id)

    def update_status(self, document_id: str, status_value: str) -> Document | None:
        document = self._repository.get_document(document_id)
        if document is None:
            return None
        document.status = status_value
        self._repository.save_document(document)
        return document

    def update_latest_job(
        self,
        document_id: str,
        job_id: str | None,
    ) -> Document | None:
        document = self._repository.get_document(document_id)
        if document is None:
            return None
        document.latest_job_id = job_id
        self._repository.save_document(document)
        return document

    def add_artifact(
        self,
        *,
        document_version_id: str,
        artifact_type: str,
        storage_path: str,
    ) -> DocumentArtifact:
        for artifact in self._repository.list_artifacts_for_version(document_version_id):
            if artifact.artifact_type == artifact_type:
                artifact.storage_path = storage_path
                self._repository.save_artifact(artifact)
                return artifact

        artifact = DocumentArtifact(
            id=self._repository.next_identifier("artifact"),
            document_version_id=document_version_id,
            artifact_type=artifact_type,
            storage_path=storage_path,
        )
        self._repository.save_artifact(artifact)
        return artifact

    def create_upload(
        self,
        *,
        current_user: AuthenticatedUser,
        project_id: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> tuple[Document, DocumentVersion, DocumentArtifact]:
        if content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF uploads are supported in Phase 1",
            )

        document_id = self._repository.next_identifier("doc")
        version_id = self._repository.next_identifier("doc-version")
        document = Document(
            id=document_id,
            organization_id=current_user.organization_id,
            project_id=project_id,
            file_name=filename,
            library_type="norm_library",
            uploaded_by=current_user.id,
            status="uploaded",
            current_version_id=version_id,
        )
        version = DocumentVersion(
            id=version_id,
            document_id=document.id,
            version_number=1,
            source_file_name=filename,
        )
        storage_path = self._storage.save_bytes(
            project_id=project_id,
            document_id=document.id,
            version_id=version.id,
            filename=filename,
            content=content,
        )
        artifact = DocumentArtifact(
            id=self._repository.next_identifier("artifact"),
            document_version_id=version.id,
            artifact_type="original_pdf",
            storage_path=storage_path,
        )
        self._repository.save_document(document)
        self._repository.save_version(version)
        self._repository.save_artifact(artifact)
        return document, version, artifact


document_service = DocumentService(repository=get_document_repository())
