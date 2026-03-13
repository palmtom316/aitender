import re

from app.models.norm_clause_entry import NormClauseEntry
from app.services.norm_page_locator import NormPageLocator
from app.services.norm_summary_builder import NormSummaryBuilder


HEADING_PATTERN = re.compile(r"^(#+)\s+(\d+(?:\.\d+)*)\s+(.+)$")
CLAUSE_PATTERN = re.compile(r"^(\d+(?:\.\d+)+)\s+(.+)$")


class NormIndexBuilder:
    def __init__(self) -> None:
        self._page_locator = NormPageLocator()
        self._summary_builder = NormSummaryBuilder()

    def build(
        self,
        *,
        document_id: str,
        markdown_text: str,
        page_texts: list[dict],
    ) -> dict:
        entries: list[NormClauseEntry] = []
        current_heading: str | None = None
        known_labels: set[str] = set()

        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                label = heading_match.group(2)
                title = heading_match.group(3)
                parent_label = None
                node_type = "chapter"
                if "." in label:
                    parent_label = label.split(".")[0]
                    node_type = "section"

                page_start, page_end = self._page_locator.locate(
                    label=label,
                    title=title,
                    page_texts=page_texts,
                )
                entries.append(
                    NormClauseEntry(
                        document_id=document_id,
                        label=label,
                        title=title,
                        node_type=node_type,
                        parent_label=parent_label,
                        page_start=page_start,
                        page_end=page_end,
                        summary_text=self._summary_builder.build(title),
                        tags=[],
                    )
                )
                known_labels.add(label)
                current_heading = label
                continue

            clause_match = CLAUSE_PATTERN.match(line)
            if not clause_match:
                continue

            label = clause_match.group(1)
            title = clause_match.group(2)
            parent_label = self._parent_for_clause(label, current_heading, known_labels)
            page_start, page_end = self._page_locator.locate(
                label=label,
                title=title,
                page_texts=page_texts,
            )
            entries.append(
                NormClauseEntry(
                    document_id=document_id,
                    label=label,
                    title=title,
                    node_type="clause",
                    parent_label=parent_label,
                    page_start=page_start,
                    page_end=page_end,
                    summary_text=self._summary_builder.build(title),
                    tags=[],
                )
            )

        entry_dicts = [entry.model_dump() for entry in entries]
        tree = self._build_tree(entry_dicts)
        return {"entries": entry_dicts, "tree": tree}

    @staticmethod
    def _parent_for_clause(
        label: str,
        current_heading: str | None,
        known_labels: set[str],
    ) -> str | None:
        if current_heading and label.startswith(f"{current_heading}."):
            return current_heading

        parts = label.split(".")
        if len(parts) > 2:
            section_label = ".".join(parts[:-1])
            if section_label in known_labels:
                return section_label

        return parts[0]

    @staticmethod
    def _build_tree(entries: list[dict]) -> list[dict]:
        nodes = {
            entry["label"]: {**entry, "children": []}
            for entry in entries
        }
        roots: list[dict] = []

        for entry in entries:
            node = nodes[entry["label"]]
            parent_label = entry["parent_label"]
            if parent_label and parent_label in nodes:
                nodes[parent_label]["children"].append(node)
            else:
                roots.append(node)

        return roots
