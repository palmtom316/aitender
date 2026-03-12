from pathlib import Path

from app.core.config import settings
from app.models.document import Document
from app.models.document_artifact import DocumentArtifact
from app.models.document_version import DocumentVersion
from app.repositories.id_factory import prefixed_uuid
from app.repositories.document_repository import DocumentRepository
from app.repositories.json_state_store import JsonStateStore


class JsonDocumentRepository(DocumentRepository):
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "documents.json",
        )
        self._store.load(default_factory=self._default_state)

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def next_identifier(self, prefix: str) -> str:
        return prefixed_uuid(prefix)

    def list_documents(self) -> list[Document]:
        state = self._store.load(default_factory=self._default_state)
        return [
            Document.model_validate(document)
            for document in state["documents"]
        ]

    def get_document(self, document_id: str) -> Document | None:
        state = self._store.load(default_factory=self._default_state)
        for document in state["documents"]:
            if document["id"] == document_id:
                return Document.model_validate(document)
        return None

    def save_document(self, document: Document) -> None:
        state = self._store.load(default_factory=self._default_state)
        for index, current in enumerate(state["documents"]):
            if current["id"] == document.id:
                state["documents"][index] = document.model_dump(mode="json")
                self._store.save(state)
                return

        state["documents"].append(document.model_dump(mode="json"))
        self._store.save(state)

    def get_current_version(self, document_id: str) -> DocumentVersion | None:
        document = self.get_document(document_id)
        if document is None or document.current_version_id is None:
            return None

        state = self._store.load(default_factory=self._default_state)
        for version in state["versions"]:
            if version["id"] == document.current_version_id:
                return DocumentVersion.model_validate(version)
        return None

    def save_version(self, version: DocumentVersion) -> None:
        state = self._store.load(default_factory=self._default_state)
        for index, current in enumerate(state["versions"]):
            if current["id"] == version.id:
                state["versions"][index] = version.model_dump()
                self._store.save(state)
                return

        state["versions"].append(version.model_dump())
        self._store.save(state)

    def list_artifacts_for_version(
        self,
        document_version_id: str,
    ) -> list[DocumentArtifact]:
        state = self._store.load(default_factory=self._default_state)
        return [
            DocumentArtifact.model_validate(artifact)
            for artifact in state["artifacts"]
            if artifact["document_version_id"] == document_version_id
        ]

    def save_artifact(self, artifact: DocumentArtifact) -> None:
        state = self._store.load(default_factory=self._default_state)
        for index, current in enumerate(state["artifacts"]):
            if current["id"] == artifact.id:
                state["artifacts"][index] = artifact.model_dump()
                self._store.save(state)
                return

        state["artifacts"].append(artifact.model_dump())
        self._store.save(state)

    @staticmethod
    def _default_state() -> dict:
        return {
            "next_id": 1,
            "documents": [],
            "versions": [],
            "artifacts": [],
        }
