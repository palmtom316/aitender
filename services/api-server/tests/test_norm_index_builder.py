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


def test_norm_index_builder_ignores_toc_lines_and_revision_sections():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    builder = NormIndexBuilder()

    result = builder.build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[
            {"page": 1, "text": "1 总则 1.0.1 总则内容。"},
            {"page": 2, "text": "1.1 范围 1.1.1 范围内容。"},
            {
                "page": 31,
                "text": (
                    "4 电力变压器、油浸电抗器 4.1 装卸、运输与就位 "
                    "4.1.3 三维冲击加速度应控制在3g左右。"
                ),
            },
            {
                "page": 46,
                "text": (
                    "修订说明 4.1.3 条文说明 "
                    "三维冲击加速度控制在3g左右是为了避免损伤内部结构。"
                ),
            },
            {
                "page": 60,
                "text": (
                    "9 其它 9.0.1 本条用于测试 修订说明后的正文样式内容不应进入正文索引。"
                ),
            },
        ],
    )

    labels = [entry["label"] for entry in result["entries"]]

    # TOC lines like "1.1 范围 (2)" should not be treated as real nodes.
    assert "1.1" in labels
    assert "4.1" in labels
    assert "1.1.1" in labels
    assert "4.1.3" in labels
    assert "9.0.1" not in labels


def test_norm_index_builder_supports_appendix_and_other_root_nodes_with_semantic_order():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_appendix.md").read_text()
    builder = NormIndexBuilder()

    result = builder.build(
        document_id="doc-1",
        markdown_text=markdown_text,
        page_texts=[
            {"page": 20, "text": "4 设备安装 4.2 本体检查 4.2.1 本体检查内容。"},
            {"page": 21, "text": "4.10 试验 4.10.1 试验内容。"},
            {"page": 22, "text": "附录A 交接记录"},
            {"page": 23, "text": "本规范用词说明"},
            {"page": 24, "text": "引用标准名录"},
        ],
    )

    labels = [entry["label"] for entry in result["entries"]]

    assert labels == [
        "4",
        "4.2",
        "4.2.1",
        "4.10",
        "4.10.1",
        "附录A",
        "本规范用词说明",
        "引用标准名录",
    ]
    appendix_entry = next(entry for entry in result["entries"] if entry["label"] == "附录A")
    wording_entry = next(
        entry for entry in result["entries"] if entry["label"] == "本规范用词说明"
    )
    standards_entry = next(
        entry for entry in result["entries"] if entry["label"] == "引用标准名录"
    )
    assert appendix_entry["node_type"] == "appendix"
    assert appendix_entry["parent_label"] is None
    assert wording_entry["node_type"] == "other"
    assert standards_entry["node_type"] == "other"
    assert [node["label"] for node in result["tree"]] == [
        "4",
        "附录A",
        "本规范用词说明",
        "引用标准名录",
    ]
