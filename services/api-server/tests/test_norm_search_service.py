from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.norm_search_service import NormSearchService


class FakeNormStructureRepository(NormStructureRepository):
    def supports_persisted_search(self) -> bool:
        return True

    def reset(self) -> None:
        return None

    def replace_clause_entries(self, document_id, entries) -> None:
        return None

    def replace_commentary_entries(self, document_id, entries) -> None:
        return None

    def list_clause_entries(self, document_id):
        return []

    def list_commentary_entries(self, document_id):
        return []

    def search_clause_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        if document_id != "doc-1":
            return None

        items = [
            {
                "label": "1.1.1",
                "title": "Scope clause text that explains the implementation scope.",
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope clause text that explains the implementation scope.",
                "commentary_summary": "Commentary for the scope clause.",
                "path_labels": ["1", "1.1", "1.1.1"],
            }
        ]
        if clause_id:
            items = [item for item in items if item["label"] == clause_id]
        if path_prefix:
            items = [
                item for item in items if path_prefix in item["path_labels"]
            ]
        if query:
            tokens = query.lower().split()
            items = [
                item
                for item in items
                if all(
                    token in (
                        f"{item['title']} {item['summary_text']} {item['commentary_summary']}"
                    ).lower()
                    for token in tokens
                )
            ]
        return items


def test_search_document_uses_repository_backed_results():
    service = NormSearchService(
        structure_repository=FakeNormStructureRepository(),
    )

    result = service.search_document(
        document_id="doc-1",
        query="implementation scope",
        path_prefix="1.1",
    )

    assert result == {
        "items": [
            {
                "label": "1.1.1",
                "title": "Scope clause text that explains the implementation scope.",
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope clause text that explains the implementation scope.",
                "commentary_summary": "Commentary for the scope clause.",
                "path_labels": ["1", "1.1", "1.1.1"],
                "tags": [],
            }
        ]
    }


def test_search_document_returns_none_when_repository_has_no_persisted_data():
    service = NormSearchService(
        structure_repository=FakeNormStructureRepository(),
    )

    result = service.search_document(document_id="missing-doc")

    assert result is None
