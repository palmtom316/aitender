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
        markdown_text = self._trim_to_first_numeric_heading(markdown_text)

        entries: list[NormCommentaryEntry] = []
        commentary_map: dict[str, str] = {}
        errors: list[str] = []
        current_heading: str | None = None
        known_labels: set[str] = set()
        skipping_toc = False

        for raw_line in markdown_text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if "目次" in line:
                skipping_toc = True
                continue

            heading_match = HEADING_PATTERN.match(line)
            if heading_match:
                skipping_toc = False
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
                        summary_text="",
                        tags=[],
                    )
                )
                known_labels.add(label)
                current_heading = label
                continue

            if skipping_toc:
                continue

            clause_match = CLAUSE_PATTERN.match(line)
            if not clause_match:
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
                    summary_text=commentary_text,
                    tags=[],
                )
            )
            commentary_map[label] = commentary_text

        entry_dicts = [entry.model_dump() for entry in entries]
        return {
            "summary_text": "",
            "tree": self._build_tree(entry_dicts),
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

    @staticmethod
    def _trim_to_first_numeric_heading(markdown_text: str) -> str:
        """
        Commentary parsing should ignore revision intro and other non-structured text.
        We only start from the first numeric heading (e.g. '# 4 ...').
        """
        lines = markdown_text.splitlines()
        for idx, raw in enumerate(lines):
            line = raw.lstrip()
            if line.startswith("# "):
                rest = line[2:].strip()
                if rest and rest[0].isdigit():
                    return "\n".join(lines[idx:]).strip()
        return markdown_text.strip()
