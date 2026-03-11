from pathlib import Path

from app.services.norm_index_builder import NormIndexBuilder


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def test_norm_index_builder_extracts_chapter_section_and_clause_entries():
    markdown_text = (FIXTURES_DIR / "sample_norm.md").read_text()
    builder = NormIndexBuilder()

    result = builder.build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[
            {"page": 1, "text": "1 General 1.0.1 General clause text for the project."},
            {
                "page": 2,
                "text": "1.1 Scope 1.1.1 Scope clause text that explains the implementation scope.",
            },
            {"page": 3, "text": "2 Safety 2.0.1 Safety clause text for on-site execution."},
        ],
    )

    entries = result["entries"]
    tree = result["tree"]

    assert [entry["label"] for entry in entries] == [
        "1",
        "1.0.1",
        "1.1",
        "1.1.1",
        "2",
        "2.0.1",
    ]
    assert tree[0]["label"] == "1"
    assert tree[0]["children"][0]["label"] == "1.0.1"
    assert tree[0]["children"][1]["label"] == "1.1"
    assert tree[1]["label"] == "2"
    assert tree[1]["children"][0]["label"] == "2.0.1"

    scope_clause = next(
        entry for entry in entries if entry["label"] == "1.1.1"
    )
    assert scope_clause["page_start"] == 2
    assert scope_clause["page_end"] == 2
    assert scope_clause["summary_text"] == "Scope clause text that explains the implementation scope."
