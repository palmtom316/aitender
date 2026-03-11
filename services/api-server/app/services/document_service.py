from itertools import count
from pathlib import Path

from fastapi import HTTPException, status

from app.integrations.storage.local import LocalObjectStorage
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.models.user import AuthenticatedUser


class DocumentService:
    def __init__(self) -> None:
        self._id_sequence = count(1)
        self._storage = LocalObjectStorage(
            Path("tmp/storage"),
        )
        self.reset()

    def reset(self) -> None:
        self._documents: list[Document] = []
        self._versions: list[DocumentVersion] = []
        self._artifacts: list[DocumentArtifact] = []
        self._storage.reset()

    def document_count(self) -> int:
        return len(self._documents)

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

        document_id = f"doc-{next(self._id_sequence)}"
        version_id = f"doc-version-{next(self._id_sequence)}"
        artifact_id = f"artifact-{next(self._id_sequence)}"

        document = Document(
            id=document_id,
            organization_id=current_user.organization_id,
            project_id=project_id,
            file_name=filename,
            library_type="norm_library",
            uploaded_by=current_user.id,
            status="uploaded",
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
            id=artifact_id,
            document_version_id=version.id,
            artifact_type="original_pdf",
            storage_path=storage_path,
        )

        self._documents.append(document)
        self._versions.append(version)
        self._artifacts.append(artifact)
        return document, version, artifact


document_service = DocumentService()
