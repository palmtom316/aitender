from app.services.norm_ai_scope_patcher import NormAiScopePatcher
from app.services.norm_workflow_validator import NormWorkflowValidator


class FakeAiStructurer:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(
        self,
        *,
        document_id: str,
        markdown_text: str,
        page_texts: list[dict],
        baseline_clause_index: dict,
        baseline_commentary_result: dict,
        config,
    ):
        self.calls.append(
            {
                "document_id": document_id,
                "markdown_text": markdown_text,
                "baseline_labels": [e["label"] for e in baseline_clause_index["entries"]],
                "baseline_commentary_labels": [
                    e["label"] for e in baseline_commentary_result["entries"]
                ],
                "page_numbers": [item["page"] for item in page_texts],
            }
        )

        # Patch in the missing section + clause so the validator can pass.
        patched_entries = list(baseline_clause_index["entries"]) + [
            {
                "document_id": document_id,
                "label": "1.1",
                "title": "Scope",
                "node_type": "section",
                "parent_label": "1",
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": document_id,
                "label": "1.1.1",
                "title": "Scope clause text",
                "node_type": "clause",
                "parent_label": "1.1",
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope clause text",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
        ]
        return (
            {
                "summary_text": "patched",
                "entries": patched_entries,
                "tree": [],
            },
            {
                "summary_text": "",
                "tree": [],
                "entries": [],
                "commentary_map": {},
                "errors": [],
            },
        )


def test_norm_ai_scope_patcher_fills_missing_expected_sections_and_revalidates():
    baseline_clause_index = {
        "summary_text": "",
        "entries": [
            {
                "document_id": "doc-1",
                "label": "1",
                "title": "General",
                "node_type": "chapter",
                "parent_label": None,
                "path_labels": [],
                "page_start": 1,
                "page_end": 1,
                "summary_text": "General",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "1.0.1",
                "title": "General clause text",
                "node_type": "clause",
                "parent_label": "1",
                "path_labels": [],
                "page_start": 1,
                "page_end": 1,
                "summary_text": "General clause text",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
        ],
        "tree": [
            {
                "label": "1",
                "children": [{"label": "1.0.1", "children": []}],
            }
        ],
    }
    baseline_commentary = {
        "summary_text": "",
        "tree": [],
        "entries": [],
        "commentary_map": {},
        "errors": [],
    }

    validator = NormWorkflowValidator()
    before = validator.validate(
        clause_index=baseline_clause_index,
        commentary_result=baseline_commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
    )
    assert before["ok"] is False

    fake_structurer = FakeAiStructurer()
    patcher = NormAiScopePatcher(ai_structurer=fake_structurer)
    clause_index, commentary = patcher.patch(
        document_id="doc-1",
        body_markdown="# 1 General",
        commentary_markdown="",
        body_page_texts=[{"page": 1, "text": "1 General"}],
        commentary_page_texts=[],
        baseline_clause_index=baseline_clause_index,
        baseline_commentary_result=baseline_commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
        config=object(),
    )

    after = validator.validate(
        clause_index=clause_index,
        commentary_result=commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
    )
    assert after["ok"] is True
    assert len(fake_structurer.calls) == 1


def test_norm_ai_scope_patcher_uses_scope_local_markdown_and_page_texts():
    baseline_clause_index = {
        "summary_text": "",
        "entries": [
            {
                "document_id": "doc-1",
                "label": "1",
                "title": "General",
                "node_type": "chapter",
                "parent_label": None,
                "path_labels": [],
                "page_start": 1,
                "page_end": 1,
                "summary_text": "General",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "1.0.1",
                "title": "General clause text",
                "node_type": "clause",
                "parent_label": "1",
                "path_labels": [],
                "page_start": 1,
                "page_end": 1,
                "summary_text": "General clause text",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "2",
                "title": "Safety",
                "node_type": "chapter",
                "parent_label": None,
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Safety",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "2.0.1",
                "title": "Safety clause text",
                "node_type": "clause",
                "parent_label": "2",
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Safety clause text",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
        ],
        "tree": [],
    }
    baseline_commentary = {
        "summary_text": "",
        "tree": [],
        "entries": [
            {
                "document_id": "doc-1",
                "label": "2",
                "title": "Safety",
                "node_type": "chapter",
                "parent_label": None,
                "page_start": 10,
                "page_end": 10,
                "commentary_text": "",
                "summary_text": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "2.0.1",
                "title": "2.0.1",
                "node_type": "clause",
                "parent_label": "2",
                "page_start": 10,
                "page_end": 10,
                "commentary_text": "Detailed safety commentary",
                "summary_text": "Detailed safety commentary",
                "tags": [],
            },
        ],
        "commentary_map": {"2.0.1": "Detailed safety commentary"},
        "errors": [],
    }

    fake_structurer = FakeAiStructurer()
    patcher = NormAiScopePatcher(ai_structurer=fake_structurer)
    patcher.patch(
        document_id="doc-1",
        body_markdown=(
            "# 1 General\n"
            "1.0.1 General clause text\n"
            "# 2 Safety\n"
            "2.0.1 Safety clause text\n"
        ),
        commentary_markdown=(
            "# 2 Safety\n"
            "2.0.1 Detailed safety commentary\n"
        ),
        body_page_texts=[
            {"page": 1, "text": "1 General 1.0.1 General clause text"},
            {"page": 2, "text": "2 Safety 2.0.1 Safety clause text"},
        ],
        commentary_page_texts=[
            {"page": 10, "text": "2 Safety 2.0.1 Detailed safety commentary"},
        ],
        baseline_clause_index=baseline_clause_index,
        baseline_commentary_result=baseline_commentary,
        expected_chapters=["1", "2"],
        expected_sections=[],
        config=object(),
    )

    assert len(fake_structurer.calls) == 3
    assert fake_structurer.calls[0]["baseline_labels"] == ["1", "1.0.1"]
    assert fake_structurer.calls[0]["page_numbers"] == [1]
    assert "General clause text" in fake_structurer.calls[0]["markdown_text"]
    assert "Safety clause text" not in fake_structurer.calls[0]["markdown_text"]

    assert fake_structurer.calls[1]["baseline_labels"] == ["2", "2.0.1"]
    assert fake_structurer.calls[1]["page_numbers"] == [2]
    assert "Safety clause text" in fake_structurer.calls[1]["markdown_text"]
    assert "General clause text" not in fake_structurer.calls[1]["markdown_text"]

    assert fake_structurer.calls[2]["baseline_labels"] == ["2", "2.0.1"]
    assert fake_structurer.calls[2]["baseline_commentary_labels"] == ["2", "2.0.1"]
    assert fake_structurer.calls[2]["page_numbers"] == [10]
    assert "Detailed safety commentary" in fake_structurer.calls[2]["markdown_text"]
    assert "General clause text" not in fake_structurer.calls[2]["markdown_text"]


def test_norm_ai_scope_patcher_merges_commentary_patch():
    baseline_clause_index = {
        "summary_text": "",
        "entries": [
            {
                "document_id": "doc-1",
                "label": "1",
                "title": "General",
                "node_type": "chapter",
                "parent_label": None,
                "path_labels": [],
                "page_start": 1,
                "page_end": 1,
                "summary_text": "General",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "1.1",
                "title": "Scope",
                "node_type": "section",
                "parent_label": "1",
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "1.1.1",
                "title": "Scope clause text",
                "node_type": "clause",
                "parent_label": "1.1",
                "path_labels": [],
                "page_start": 2,
                "page_end": 2,
                "summary_text": "Scope clause text",
                "commentary_summary": "",
                "content_preview": "",
                "tags": [],
            },
        ],
        "tree": [],
    }
    baseline_commentary = {
        "summary_text": "",
        "tree": [
            {
                "label": "1",
                "children": [{"label": "1.1", "children": []}],
            }
        ],
        "entries": [
            {
                "document_id": "doc-1",
                "label": "1",
                "title": "General",
                "node_type": "chapter",
                "parent_label": None,
                "page_start": 10,
                "page_end": 10,
                "commentary_text": "",
                "summary_text": "",
                "tags": [],
            },
            {
                "document_id": "doc-1",
                "label": "1.1",
                "title": "Scope",
                "node_type": "section",
                "parent_label": "1",
                "page_start": 10,
                "page_end": 10,
                "commentary_text": "",
                "summary_text": "",
                "tags": [],
            },
        ],
        "commentary_map": {},
        "errors": [],
    }

    class CommentaryPatchStructurer(FakeAiStructurer):
        def generate(self, **kwargs):
            self.calls.append(
                {
                    "baseline_labels": [
                        entry["label"]
                        for entry in kwargs["baseline_clause_index"]["entries"]
                    ],
                    "baseline_commentary_labels": [
                        entry["label"]
                        for entry in kwargs["baseline_commentary_result"]["entries"]
                    ],
                }
            )
            return (
                kwargs["baseline_clause_index"],
                {
                    "summary_text": "patched commentary",
                    "tree": [],
                    "entries": [
                        {
                            "document_id": "doc-1",
                            "label": "1.1.1",
                            "title": "1.1.1",
                            "node_type": "clause",
                            "parent_label": "1.1",
                            "page_start": 10,
                            "page_end": 10,
                            "commentary_text": "Detailed scope commentary",
                            "summary_text": "Detailed scope commentary",
                            "tags": ["explanation"],
                        }
                    ],
                    "commentary_map": {"1.1.1": "Detailed scope commentary"},
                    "errors": [],
                },
            )

    validator = NormWorkflowValidator()
    before = validator.validate(
        clause_index=baseline_clause_index,
        commentary_result=baseline_commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
    )
    assert before["ok"] is False

    clause_index, commentary = NormAiScopePatcher(
        ai_structurer=CommentaryPatchStructurer()
    ).patch(
        document_id="doc-1",
        body_markdown="# 1 General\n## 1.1 Scope\n1.1.1 Scope clause text",
        commentary_markdown="# 1 General\n## 1.1 Scope\n1.1.1 Detailed scope commentary",
        body_page_texts=[{"page": 2, "text": "1.1.1 Scope clause text"}],
        commentary_page_texts=[{"page": 10, "text": "1.1.1 Detailed scope commentary"}],
        baseline_clause_index=baseline_clause_index,
        baseline_commentary_result=baseline_commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
        config=object(),
    )

    after = validator.validate(
        clause_index=clause_index,
        commentary_result=commentary,
        expected_chapters=["1"],
        expected_sections=["1.1"],
    )
    assert after["ok"] is True
    assert commentary["commentary_map"]["1.1.1"] == "Detailed scope commentary"
    assert any(
        entry["label"] == "1.1.1" and entry["commentary_summary"] == "Detailed scope commentary"
        for entry in clause_index["entries"]
    )
