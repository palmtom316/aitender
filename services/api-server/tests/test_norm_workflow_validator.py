from pathlib import Path

from app.services.norm_commentary_builder import NormCommentaryBuilder
from app.services.norm_index_builder import NormIndexBuilder
from app.services.norm_markdown_splitter import NormMarkdownSplitter
from app.services.norm_toc_parser import NormTocParser
from app.services.norm_workflow_validator import NormWorkflowValidator


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def test_norm_workflow_validator_accepts_complete_structure_from_fixture():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    segments = NormMarkdownSplitter().split(markdown_text)
    toc = NormTocParser().parse_expected_labels(segments.toc_markdown)

    clause_index = NormIndexBuilder().build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[
            {"page": 1, "text": "1 总则 1.0.1 总则内容。"},
            {"page": 2, "text": "1.1 范围 1.1.1 范围内容。"},
            {"page": 31, "text": "4 4.1 4.1.3 三维冲击加速度应控制在3g左右。"},
            {"page": 46, "text": "4.1.3 条文说明 三维冲击加速度控制在3g左右是为了避免损伤内部结构。"},
        ],
    )
    commentary_markdown = segments.commentary_markdown.split("# 9 其它")[0].strip()
    commentary = NormCommentaryBuilder().build(
        document_id="doc-1",
        markdown_text=commentary_markdown,
        page_texts=[
            {"page": 46, "text": "4.1.3 条文说明 三维冲击加速度控制在3g左右是为了避免损伤内部结构。"},
        ],
    )

    result = NormWorkflowValidator().validate(
        clause_index=clause_index,
        commentary_result=commentary,
        expected_chapters=toc["expected_chapters"],
        expected_sections=toc["expected_sections"],
    )
    assert result["ok"] is True
    assert result["errors"] == []


def test_norm_workflow_validator_reports_missing_expected_sections():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    segments = NormMarkdownSplitter().split(markdown_text)
    toc = NormTocParser().parse_expected_labels(segments.toc_markdown)

    clause_index = NormIndexBuilder().build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[],
    )
    # Remove a required section label to simulate incomplete parsing.
    clause_index["entries"] = [
        entry for entry in clause_index["entries"] if entry["label"] != "4.1"
    ]
    clause_index["tree"] = NormIndexBuilder._build_tree(clause_index["entries"])

    result = NormWorkflowValidator().validate(
        clause_index=clause_index,
        commentary_result={"commentary_map": {}},
        expected_chapters=toc["expected_chapters"],
        expected_sections=toc["expected_sections"],
    )
    assert result["ok"] is False
    assert any("Missing expected section labels" in item for item in result["errors"])


def test_norm_workflow_validator_rejects_commentary_mapping_unknown_clause():
    result = NormWorkflowValidator().validate(
        clause_index={
            "entries": [
                {
                    "label": "1.0.1",
                    "node_type": "clause",
                    "parent_label": "1",
                }
            ],
            "tree": [{"label": "1.0.1", "children": []}],
        },
        commentary_result={"commentary_map": {"9.9.9": "bad"}},
        expected_chapters=None,
        expected_sections=None,
    )
    assert result["ok"] is False
    assert "Commentary references unknown clause: 9.9.9" in result["errors"]
