from pathlib import Path

from app.services.norm_markdown_splitter import NormMarkdownSplitter


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def test_norm_markdown_splitter_splits_toc_body_and_commentary_segments():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    splitter = NormMarkdownSplitter()

    segments = splitter.split(markdown_text)

    assert "目次" in segments.toc_markdown
    assert "1.1 范围 (2)" in segments.toc_markdown
    assert "# 1 总则" not in segments.toc_markdown

    assert segments.body_markdown.startswith("# 1 总则")
    assert "目次" not in segments.body_markdown
    assert "修订说明" not in segments.body_markdown
    assert "4.1.3 三维冲击加速度应控制在3g左右。" in segments.body_markdown

    assert segments.commentary_markdown.startswith("# 修订说明")
    assert "条文说明" in segments.commentary_markdown

