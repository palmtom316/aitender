from abc import ABC, abstractmethod

from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry


class NormStructureRepository(ABC):
    @abstractmethod
    def supports_persisted_search(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def replace_clause_entries(
        self,
        document_id: str,
        entries: list[NormClauseEntry],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def replace_commentary_entries(
        self,
        document_id: str,
        entries: list[NormCommentaryEntry],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_clause_entries(self, document_id: str) -> list[NormClauseEntry]:
        raise NotImplementedError

    @abstractmethod
    def list_commentary_entries(
        self,
        document_id: str,
    ) -> list[NormCommentaryEntry]:
        raise NotImplementedError

    @abstractmethod
    def search_clause_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        raise NotImplementedError
