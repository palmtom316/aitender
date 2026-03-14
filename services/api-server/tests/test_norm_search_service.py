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

    def search_commentary_results(
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
                "content_preview": "",
                "path_labels": ["1", "1.1", "1.1.1"],
                "tags": [],
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
                if all(token in item["commentary_summary"].lower() for token in tokens)
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
                "content_preview": "",
                "path_labels": ["1", "1.1", "1.1.1"],
                "tags": [],
            }
        ],
        "commentary_items": []
    }


def test_search_document_returns_none_when_repository_has_no_persisted_data():
    service = NormSearchService(
        structure_repository=FakeNormStructureRepository(),
    )

    result = service.search_document(document_id="missing-doc")

    assert result is None


def test_search_sorts_clause_results_semantically():
    service = NormSearchService()

    result = service.search(
        document_id="doc-1",
        clause_index={
            "entries": [
                {
                    "document_id": "doc-1",
                    "label": "4.10.1",
                    "title": "试验内容",
                    "node_type": "clause",
                    "parent_label": "4.10",
                    "page_start": 21,
                    "page_end": 21,
                    "summary_text": "试验内容",
                    "commentary_summary": "",
                    "content_preview": "",
                    "tags": [],
                },
                {
                    "document_id": "doc-1",
                    "label": "4.2.1",
                    "title": "本体检查内容",
                    "node_type": "clause",
                    "parent_label": "4.2",
                    "page_start": 20,
                    "page_end": 20,
                    "summary_text": "本体检查内容",
                    "commentary_summary": "",
                    "content_preview": "",
                    "tags": [],
                },
            ],
            "tree": [],
        },
        commentary_result={"commentary_map": {}},
    )

    assert [item["label"] for item in result["items"]] == ["4.2.1", "4.10.1"]
    assert result["commentary_items"] == []


def test_search_separates_clause_hits_from_commentary_hits():
    service = NormSearchService()

    result = service.search(
        document_id="doc-1",
        clause_index={
            "entries": [
                {
                    "document_id": "doc-1",
                    "label": "1.1.1",
                    "title": "Scope clause text",
                    "node_type": "clause",
                    "parent_label": "1.1",
                    "page_start": 2,
                    "page_end": 2,
                    "summary_text": "正文没有这个关键词",
                    "commentary_summary": "",
                    "content_preview": "",
                    "path_labels": ["1", "1.1", "1.1.1"],
                    "tags": [],
                }
            ],
            "tree": [],
        },
        commentary_result={"commentary_map": {"1.1.1": "三维冲击加速度控制在3g左右。"}},
        query="3g",
    )

    assert result["items"] == []
    assert [item["label"] for item in result["commentary_items"]] == ["1.1.1"]
