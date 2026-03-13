import json
from pathlib import Path

from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.factory import get_norm_structure_repository
from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.document_service import DocumentService, document_service
from app.services.norm_search_service import NormSearchService, norm_search_service


class NormLibraryService:
    def __init__(
        self,
        *,
        documents: DocumentService = document_service,
        search_service: NormSearchService | None = None,
        structure_repository: NormStructureRepository | None = None,
    ) -> None:
        self._documents = documents
        self._structure_repository = structure_repository or get_norm_structure_repository()
        self._search = search_service or NormSearchService(
            structure_repository=self._structure_repository,
        )

    def list_documents(self, *, project_id: str) -> list[dict]:
        return [
            {
                "id": document.id,
                "file_name": document.file_name,
                "latest_job_id": document.latest_job_id,
                "status": document.status,
                "library_type": document.library_type,
            }
            for document in self._documents.list_documents(
                project_id=project_id,
                library_type="norm_library",
            )
        ]

    def get_bundle(self, *, project_id: str, document_id: str) -> dict | None:
        document = self._documents.get_document(document_id)
        if document is None or document.project_id != project_id:
            return None

        clause_index, commentary_result = self._load_structured_artifacts(document_id)
        persisted_result = self._search.search_document(
            document_id=document_id,
        )
        return {
            "document": {
                "id": document.id,
                "file_name": document.file_name,
                "latest_job_id": document.latest_job_id,
                "status": document.status,
                "library_type": document.library_type,
            },
            "tree": clause_index.get("tree", []),
            "results": persisted_result["items"]
            if persisted_result is not None
            else self._search.search(
                document_id=document_id,
                clause_index=clause_index,
                commentary_result=commentary_result,
            )["items"],
        }

    def search(
        self,
        *,
        project_id: str,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> dict | None:
        document = self._documents.get_document(document_id)
        if document is None or document.project_id != project_id:
            return None

        persisted_result = self._search.search_document(
            document_id=document_id,
            query=query,
            clause_id=clause_id,
            path_prefix=path_prefix,
        )
        if persisted_result is not None:
            return persisted_result

        clause_index, commentary_result = self._load_structured_artifacts(document_id)
        return self._search.search(
            document_id=document_id,
            clause_index=clause_index,
            commentary_result=commentary_result,
            query=query,
            clause_id=clause_id,
            path_prefix=path_prefix,
        )

    def _load_structured_artifacts(self, document_id: str) -> tuple[dict, dict]:
        clause_entries = self._structure_repository.list_clause_entries(document_id)
        commentary_entries = self._structure_repository.list_commentary_entries(document_id)
        if clause_entries:
            return (
                self._clause_index_from_entries(clause_entries),
                self._commentary_result_from_entries(commentary_entries),
            )

        version = self._documents.get_current_version(document_id)
        if version is None:
            return (
                {"entries": [], "tree": []},
                {
                    "summary_text": "",
                    "tree": [],
                    "entries": [],
                    "commentary_map": {},
                    "errors": [],
                },
            )

        artifacts = {
            artifact.artifact_type: artifact
            for artifact in self._documents.list_artifacts_for_version(version.id)
        }
        clause_index = self._load_json_artifact(
            artifacts.get("clause_index_json"),
            default={"entries": [], "tree": []},
        )
        commentary_result = self._load_json_artifact(
            artifacts.get("commentary_json"),
            default={
                "summary_text": "",
                "tree": [],
                "entries": [],
                "commentary_map": {},
                "errors": [],
            },
        )
        return clause_index, commentary_result

    @staticmethod
    def _load_json_artifact(artifact, *, default: dict) -> dict:
        if artifact is None:
            return default

        artifact_path = Path(artifact.storage_path)
        if not artifact_path.exists():
            return default

        return json.loads(artifact_path.read_text())

    @staticmethod
    def _clause_index_from_entries(entries: list[NormClauseEntry]) -> dict:
        entry_dicts = [entry.model_dump(mode="json") for entry in entries]
        nodes = {
            entry["label"]: {**entry, "children": []}
            for entry in entry_dicts
        }
        roots: list[dict] = []

        for entry in entry_dicts:
            node = nodes[entry["label"]]
            parent_label = entry.get("parent_label")
            if parent_label and parent_label in nodes:
                nodes[parent_label]["children"].append(node)
            else:
                roots.append(node)

        return {"entries": entry_dicts, "tree": roots}

    @staticmethod
    def _commentary_result_from_entries(
        entries: list[NormCommentaryEntry],
    ) -> dict:
        entry_dicts = [entry.model_dump(mode="json") for entry in entries]
        nodes = {
            entry["label"]: {**entry, "children": []}
            for entry in entry_dicts
        }
        roots: list[dict] = []

        for entry in entry_dicts:
            node = nodes[entry["label"]]
            parent_label = entry.get("parent_label")
            if parent_label and parent_label in nodes:
                nodes[parent_label]["children"].append(node)
            else:
                roots.append(node)

        return {
            "summary_text": "",
            "entries": entry_dicts,
            "tree": roots,
            "commentary_map": {
                entry.label: entry.commentary_text
                for entry in entries
                if entry.node_type == "clause"
            },
            "errors": [],
        }


norm_library_service = NormLibraryService()
