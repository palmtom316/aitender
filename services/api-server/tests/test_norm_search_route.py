import pytest
from fastapi import HTTPException

from app.api.routes.norm_search import NormSearchRequest, query_norm


class FakeNormSearchService:
    def __init__(self, persisted_result: dict | None = None) -> None:
        self.persisted_result = persisted_result
        self.persisted_calls: list[dict] = []
        self.legacy_calls: list[dict] = []

    def search_document(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> dict | None:
        self.persisted_calls.append(
            {
                "document_id": document_id,
                "query": query,
                "clause_id": clause_id,
                "path_prefix": path_prefix,
            }
        )
        return self.persisted_result

    def search(
        self,
        *,
        document_id: str,
        clause_index: dict,
        commentary_result: dict,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> dict:
        self.legacy_calls.append(
            {
                "document_id": document_id,
                "clause_index": clause_index,
                "commentary_result": commentary_result,
                "query": query,
                "clause_id": clause_id,
                "path_prefix": path_prefix,
            }
        )
        return {"items": []}


def test_query_norm_uses_repository_backed_search_when_payload_omits_json(monkeypatch):
    fake_service = FakeNormSearchService(
        persisted_result={
            "items": [
                {
                    "label": "1.1.1",
                    "title": "Scope clause text that explains the implementation scope.",
                    "page_start": 2,
                    "page_end": 2,
                    "summary_text": "Scope clause text that explains the implementation scope.",
                    "commentary_summary": "",
                    "path_labels": ["1", "1.1", "1.1.1"],
                }
            ]
        }
    )
    monkeypatch.setattr("app.api.routes.norm_search.norm_search_service", fake_service)

    result = query_norm(
        NormSearchRequest(
            document_id="doc-1",
            query="implementation scope",
            path_prefix="1.1",
        )
    )

    assert fake_service.persisted_calls == [
        {
            "document_id": "doc-1",
            "query": "implementation scope",
            "clause_id": None,
            "path_prefix": "1.1",
        }
    ]
    assert result["items"][0]["label"] == "1.1.1"


def test_query_norm_rejects_missing_json_when_no_persisted_data(monkeypatch):
    fake_service = FakeNormSearchService(persisted_result=None)
    monkeypatch.setattr("app.api.routes.norm_search.norm_search_service", fake_service)

    with pytest.raises(HTTPException) as exc_info:
        query_norm(
            NormSearchRequest(
                document_id="missing-doc",
                query="scope",
            )
        )

    assert exc_info.value.status_code == 400
    assert "persisted norm search data" in exc_info.value.detail
