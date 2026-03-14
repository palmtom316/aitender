import re


TOC_LINE_PATTERN = re.compile(r"^(?P<label>\d+(?:\.\d+)*)\s+")


class NormTocParser:
    def parse_expected_labels(self, toc_markdown: str) -> dict[str, list[str]]:
        """
        Extract expected chapter/section labels from a TOC block.

        We only keep:
        - chapter labels: "4"
        - section labels: "4.1"

        Clause labels (two or more dots) are ignored on purpose.
        """

        expected_chapters: list[str] = []
        expected_sections: list[str] = []

        for raw_line in toc_markdown.splitlines():
            line = raw_line.strip()
            if not line or "目次" in line:
                continue

            match = TOC_LINE_PATTERN.match(line)
            if not match:
                continue

            label = match.group("label")
            dot_count = label.count(".")
            if dot_count == 0:
                if label not in expected_chapters:
                    expected_chapters.append(label)
            elif dot_count == 1:
                if label not in expected_sections:
                    expected_sections.append(label)

        return {
            "expected_chapters": expected_chapters,
            "expected_sections": expected_sections,
        }

