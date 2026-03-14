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
        config,
    ):
        self.calls.append(
            {
                "document_id": document_id,
                "markdown_text": markdown_text,
                "baseline_labels": [e["label"] for e in baseline_clause_index["entries"]],
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
        markdown_text="# 1 General",
        page_texts=[{"page": 1, "text": "1 General"}],
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

