from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.norm_commentary_builder import NormCommentaryBuilder
from app.services.norm_index_builder import NormIndexBuilder


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def _build_payload() -> dict:
    norm_markdown = (FIXTURES_DIR / "sample_norm.md").read_text()
    commentary_markdown = (FIXTURES_DIR / "sample_commentary.md").read_text()
    page_texts = [
        {"page": 1, "text": "1 General 1.0.1 General clause text for the project."},
        {
            "page": 2,
            "text": "1.1 Scope 1.1.1 Scope clause text that explains the implementation scope.",
        },
        {"page": 3, "text": "2 Safety 2.0.1 Safety clause text for on-site execution."},
        {"page": 10, "text": "1 General 1.0.1 Commentary for the general clause."},
        {
            "page": 11,
            "text": "1.1 Scope 1.1.1 Commentary for the scope clause.",
        },
        {"page": 12, "text": "2 Safety 2.0.1 Commentary for the safety clause."},
    ]

    return {
        "document_id": "doc-1",
        "clause_index": NormIndexBuilder().build(
            document_id="doc-1",
            markdown_text=norm_markdown,
            page_texts=page_texts,
        ),
        "commentary_result": NormCommentaryBuilder().build(
            document_id="doc-1",
            markdown_text=commentary_markdown,
            page_texts=page_texts,
        ),
    }


def test_norm_search_supports_keyword_search_and_returns_preview_fields():
    client = TestClient(app)

    response = client.post(
        "/norm-search/query",
        json={
            **_build_payload(),
            "query": "implementation scope",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
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
    }


def test_norm_search_supports_clause_id_and_path_prefix_filters():
    client = TestClient(app)

    response = client.post(
        "/norm-search/query",
        json={
            **_build_payload(),
            "query": "clause",
            "clause_id": "1.1.1",
            "path_prefix": "1.1",
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == [
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
