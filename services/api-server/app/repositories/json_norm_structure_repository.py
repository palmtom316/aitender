from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.norm_structure_repository import NormStructureRepository


class JsonNormStructureRepository(NormStructureRepository):
    def supports_persisted_search(self) -> bool:
        return False

    def reset(self) -> None:
        return None

    def replace_clause_entries(
        self,
        document_id: str,
        entries: list[NormClauseEntry],
    ) -> None:
        return None

    def replace_commentary_entries(
        self,
        document_id: str,
        entries: list[NormCommentaryEntry],
    ) -> None:
        return None

    def list_clause_entries(self, document_id: str) -> list[NormClauseEntry]:
        return []

    def list_commentary_entries(
        self,
        document_id: str,
    ) -> list[NormCommentaryEntry]:
        return []

    def search_clause_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        return None
