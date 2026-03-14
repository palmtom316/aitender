from dataclasses import dataclass


@dataclass(frozen=True)
class NormMarkdownSegments:
    toc_markdown: str
    body_markdown: str
    commentary_markdown: str


class NormMarkdownSplitter:
    """
    Split a MinerU-like norm markdown into:
    - toc_markdown: the first "目次" block (if any)
    - body_markdown:正文条款区域 (before "修订说明")
    - commentary_markdown: everything after "修订说明" (may include revision intro + 2nd TOC)
    """

    def split(self, markdown_text: str) -> NormMarkdownSegments:
        lines = markdown_text.splitlines()

        toc_start = self._find_first_line_index(lines, lambda l: "目次" in l.strip())
        revision_start = self._find_first_line_index(
            lines, lambda l: "修订说明" in l.strip()
        )

        body_start = self._find_first_body_heading_index(lines, after=toc_start)

        toc_markdown = ""
        if toc_start is not None and body_start is not None and toc_start < body_start:
            toc_markdown = "\n".join(lines[toc_start:body_start]).strip()

        if body_start is None:
            body_markdown = markdown_text.strip()
        else:
            body_end = revision_start if revision_start is not None else len(lines)
            body_markdown = "\n".join(lines[body_start:body_end]).strip()

        commentary_markdown = ""
        if revision_start is not None:
            commentary_markdown = "\n".join(lines[revision_start:]).strip()

        return NormMarkdownSegments(
            toc_markdown=toc_markdown,
            body_markdown=body_markdown,
            commentary_markdown=commentary_markdown,
        )

    @staticmethod
    def _find_first_line_index(lines: list[str], predicate) -> int | None:
        for idx, raw in enumerate(lines):
            if predicate(raw):
                return idx
        return None

    @staticmethod
    def _find_first_body_heading_index(lines: list[str], *, after: int | None) -> int | None:
        start = (after + 1) if after is not None else 0
        for idx in range(start, len(lines)):
            line = lines[idx].lstrip()
            # First numeric chapter heading, e.g. "# 1 总则"
            if line.startswith("# "):
                rest = line[2:].strip()
                if rest and rest[0].isdigit():
                    return idx
        return None

