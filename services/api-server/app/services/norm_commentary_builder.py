import re

from app.models.norm_commentary_entry import NormCommentaryEntry
from app.services.norm_page_locator import NormPageLocator


HEADING_PATTERN = re.compile(r"^(#+)\s+(\d+(?:\.\d+)*)\s+(.+)$")
CLAUSE_PATTERN = re.compile(r"^(\d+(?:\.\d+)+)\s+(.+)$")


class NormCommentaryBuilder:
    def __init__(self) -> None:
        self._page_locator = NormPageLocator()

    def build(
        self,
        *,
        document_id: str,
        markdown_text: str,
        page_texts: list[dict],
    ) -> dict:
        entries: list[NormCommentaryEntry] = []
        commentary_map: dict[str, str] = {}
        errors: list[str] = []
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
                    NormCommentaryEntry(
                        document_id=document_id,
                        label=label,
                        title=title,
                        node_type=node_type,
                        parent_label=parent_label,
                        page_start=page_start,
                        page_end=page_end,
                        commentary_text="",
                    )
                )
                known_labels.add(label)
                current_heading = label
                continue

            clause_match = CLAUSE_PATTERN.match(line)
            if not clause_match:
                errors.append(f"Malformed commentary line: {line}")
                continue

            label = clause_match.group(1)
            commentary_text = clause_match.group(2)
            if label in commentary_map:
                errors.append(f"Duplicate commentary clause label: {label}")
                continue
            parent_label = self._parent_for_clause(label, current_heading, known_labels)
            page_start, page_end = self._page_locator.locate(
                label=label,
                title=commentary_text,
                page_texts=page_texts,
            )
            entries.append(
                NormCommentaryEntry(
                    document_id=document_id,
                    label=label,
                    title=label,
                    node_type="clause",
                    parent_label=parent_label,
                    page_start=page_start,
                    page_end=page_end,
                    commentary_text=commentary_text,
                )
            )
            commentary_map[label] = commentary_text

        entry_dicts = [entry.model_dump() for entry in entries]
        return {
            "entries": entry_dicts,
            "commentary_map": commentary_map,
            "errors": errors,
        }

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
