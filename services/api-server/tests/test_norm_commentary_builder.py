from pathlib import Path

from app.services.norm_commentary_builder import NormCommentaryBuilder


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def test_commentary_builder_creates_clause_commentary_map():
    markdown_text = (FIXTURES_DIR / "sample_commentary.md").read_text()
    builder = NormCommentaryBuilder()

    result = builder.build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[
            {"page": 10, "text": "1 General 1.0.1 Commentary for the general clause."},
            {
                "page": 11,
                "text": "1.1 Scope 1.1.1 Commentary for the scope clause.",
            },
            {"page": 12, "text": "2 Safety 2.0.1 Commentary for the safety clause."},
        ],
    )

    assert result["commentary_map"] == {
        "1.0.1": "Commentary for the general clause.",
        "1.1.1": "Commentary for the scope clause.",
        "2.0.1": "Commentary for the safety clause.",
    }
    assert [entry["label"] for entry in result["entries"]] == [
        "1",
        "1.0.1",
        "1.1",
        "1.1.1",
        "2",
        "2.0.1",
    ]
    assert result["errors"] == []


def test_commentary_builder_reports_duplicate_clause_ids_as_dirty_input():
    builder = NormCommentaryBuilder()

    result = builder.build(
        document_id="doc-1",
        markdown_text="# 1 General\n1.0.1 First commentary.\n1.0.1 Duplicate commentary.",
        page_texts=[
            {"page": 10, "text": "1 General 1.0.1 First commentary."},
        ],
    )

    assert result["errors"] == [
        "Duplicate commentary clause label: 1.0.1"
    ]


def test_commentary_builder_ignores_second_toc_blocks_in_commentary_markdown():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    # For now, approximate the commentary slice by starting after "修订说明".
    revision_idx = markdown_text.find("修订说明")
    assert revision_idx != -1
    commentary_markdown = markdown_text[revision_idx:]

    builder = NormCommentaryBuilder()
    result = builder.build(
        document_id="doc-1",
        markdown_text=commentary_markdown,
        page_texts=[
            {
                "page": 46,
                "text": (
                    "4.1.3 条文说明 三维冲击加速度控制在3g左右是为了避免损伤内部结构。"
                ),
            },
        ],
    )

    # The second TOC contains "4.1.3 三维冲击..." which must not be treated as commentary text.
    assert result["commentary_map"].get("4.1.3") == (
        "条文说明：三维冲击加速度控制在3g左右是为了避免损伤内部结构。"
    )
