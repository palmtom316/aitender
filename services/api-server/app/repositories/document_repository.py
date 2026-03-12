from abc import ABC, abstractmethod

from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion


class DocumentRepository(ABC):
    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def next_identifier(self, prefix: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_documents(self) -> list[Document]:
        raise NotImplementedError

    @abstractmethod
    def get_document(self, document_id: str) -> Document | None:
        raise NotImplementedError

    @abstractmethod
    def save_document(self, document: Document) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_current_version(self, document_id: str) -> DocumentVersion | None:
        raise NotImplementedError

    @abstractmethod
    def save_version(self, version: DocumentVersion) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_artifacts_for_version(
        self,
        document_version_id: str,
    ) -> list[DocumentArtifact]:
        raise NotImplementedError

    @abstractmethod
    def save_artifact(self, artifact: DocumentArtifact) -> None:
        raise NotImplementedError
