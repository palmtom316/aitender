from pathlib import Path

from app.services.norm_markdown_splitter import NormMarkdownSplitter
from app.services.norm_toc_parser import NormTocParser


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_samples"


def test_norm_toc_parser_extracts_expected_chapters_and_sections():
    markdown_text = (FIXTURES_DIR / "sample_norm_with_toc_and_revision.md").read_text()
    segments = NormMarkdownSplitter().split(markdown_text)

    parsed = NormTocParser().parse_expected_labels(segments.toc_markdown)

    assert parsed["expected_chapters"] == ["1", "4"]
    assert parsed["expected_sections"] == ["1.1", "4.1"]

