from __future__ import annotations

from dataclasses import dataclass

from app.services.norm_index_builder import NormIndexBuilder
from app.services.norm_label_utils import label_sort_key


@dataclass(frozen=True)
class NormScope:
    name: str
    kind: str
    chapter_label: str | None


class NormAiScopePatcher:
    """
    Scope-based AI patcher.

    Phase 1 implementation:
    - Split by expected chapter labels (from TOC).
    - Call the configured AI for each scope to patch missing/low-quality nodes.
    - Merge AI entries into the baseline and rebuild the tree locally.
    """

    def __init__(self, *, ai_structurer) -> None:
        self._ai = ai_structurer

    def patch(
        self,
        *,
        document_id: str,
        body_markdown: str,
        commentary_markdown: str,
        body_page_texts: list[dict],
        commentary_page_texts: list[dict],
        baseline_clause_index: dict,
        baseline_commentary_result: dict,
        expected_chapters: list[str],
        expected_sections: list[str],
        config,
    ) -> tuple[dict, dict]:
        scopes = self._plan_scopes(
            expected_chapters=expected_chapters,
            commentary_markdown=commentary_markdown,
        )
        baseline_by_label = {
            entry.get("label"): entry
            for entry in baseline_clause_index.get("entries", [])
            if entry.get("label")
        }
        merged_by_label = dict(baseline_by_label)
        commentary_by_label = {
            entry.get("label"): entry
            for entry in baseline_commentary_result.get("entries", [])
            if entry.get("label")
        }
        merged_commentary_by_label = dict(commentary_by_label)
        merged_commentary_map = dict(
            baseline_commentary_result.get("commentary_map", {}) or {}
        )
        commentary_summary_text = str(
            baseline_commentary_result.get("summary_text", "")
        )

        for scope in scopes:
            scope_baseline = self._slice_baseline_for_scope(
                baseline_clause_index,
                chapter_label=scope.chapter_label,
            )
            scope_baseline_commentary = self._slice_commentary_for_scope(
                baseline_commentary_result,
                chapter_label=scope.chapter_label,
            )
            scope_markdown = self._slice_markdown_for_scope(
                markdown_text=body_markdown
                if scope.kind == "body"
                else commentary_markdown,
                chapter_label=scope.chapter_label,
            )
            scope_page_texts = self._slice_page_texts_for_scope(
                page_texts=body_page_texts
                if scope.kind == "body"
                else commentary_page_texts,
                clause_index=scope_baseline,
                commentary_result=scope_baseline_commentary,
                chapter_label=scope.chapter_label,
            )
            if not scope_markdown.strip() and not scope_page_texts:
                continue
            clause_index_patch, commentary_patch = self._ai.generate(
                document_id=document_id,
                markdown_text=scope_markdown,
                page_texts=scope_page_texts,
                baseline_clause_index=scope_baseline,
                baseline_commentary_result=scope_baseline_commentary,
                config=config,
            )

            for raw in clause_index_patch.get("entries", []):
                label = str(raw.get("label", "")).strip()
                if not label:
                    continue
                if label in merged_by_label:
                    merged_by_label[label] = self._overlay_entry(
                        merged_by_label[label],
                        raw,
                    )
                else:
                    # Only accept new nodes when they belong to the TOC-expected tree.
                    if self._eligible_new_label(label, expected_chapters, expected_sections):
                        merged_by_label[label] = raw

            patch_summary_text = str(commentary_patch.get("summary_text", "")).strip()
            if patch_summary_text:
                commentary_summary_text = patch_summary_text

            for raw in commentary_patch.get("entries", []):
                label = str(raw.get("label", "")).strip()
                if not label:
                    continue
                if label in merged_commentary_by_label:
                    merged_commentary_by_label[label] = self._overlay_commentary_entry(
                        merged_commentary_by_label[label],
                        raw,
                    )
                elif self._eligible_new_label(label, expected_chapters, expected_sections):
                    merged_commentary_by_label[label] = raw

            for label, text in dict(commentary_patch.get("commentary_map", {}) or {}).items():
                normalized = str(label).strip()
                if not normalized:
                    continue
                if self._eligible_new_label(
                    normalized,
                    expected_chapters,
                    expected_sections,
                ):
                    merged_commentary_map[normalized] = str(text)

        merged_entries = list(merged_by_label.values())
        merged_entries.sort(key=lambda item: label_sort_key(str(item.get("label", ""))))
        tree = NormIndexBuilder._build_tree(merged_entries)

        clause_labels = {
            str(entry.get("label", "")).strip()
            for entry in merged_entries
            if entry.get("node_type") == "clause" and entry.get("label")
        }
        merged_commentary_entries = [
            entry
            for entry in merged_commentary_by_label.values()
            if (
                entry.get("node_type") != "clause"
                or str(entry.get("label", "")).strip() in clause_labels
            )
        ]
        merged_commentary_entries.sort(
            key=lambda item: label_sort_key(str(item.get("label", "")))
        )
        merged_commentary_map = {
            label: text
            for label, text in merged_commentary_map.items()
            if label in clause_labels
        }

        for entry in merged_entries:
            if entry.get("node_type") == "clause":
                entry["commentary_summary"] = merged_commentary_map.get(
                    str(entry.get("label", "")).strip(),
                    "",
                )

        return (
            {
                "summary_text": str(baseline_clause_index.get("summary_text", "")),
                "entries": merged_entries,
                "tree": tree,
            },
            {
                "summary_text": commentary_summary_text,
                "entries": merged_commentary_entries,
                "tree": self._build_tree(merged_commentary_entries),
                "commentary_map": merged_commentary_map,
                "errors": list(baseline_commentary_result.get("errors", [])),
            },
        )

    @staticmethod
    def _plan_scopes(
        *,
        expected_chapters: list[str],
        commentary_markdown: str,
    ) -> list[NormScope]:
        chapters = [label for label in expected_chapters if label]
        if not chapters:
            scopes = [NormScope(name="body-all", kind="body", chapter_label=None)]
        else:
            scopes = [
                NormScope(name=f"body-{label}", kind="body", chapter_label=label)
                for label in chapters
            ]
        for label in chapters:
            if f"# {label} " in commentary_markdown or f"## {label}." in commentary_markdown:
                scopes.append(
                    NormScope(
                        name=f"commentary-{label}",
                        kind="commentary",
                        chapter_label=label,
                    )
                )
        return scopes

    @staticmethod
    def _slice_baseline_for_scope(baseline: dict, *, chapter_label: str | None) -> dict:
        if chapter_label is None:
            return baseline
        prefix = f"{chapter_label}."
        entries = [
            entry
            for entry in baseline.get("entries", [])
            if entry.get("label") == chapter_label
            or str(entry.get("label", "")).startswith(prefix)
        ]
        return {
            "summary_text": str(baseline.get("summary_text", "")),
            "entries": entries,
            "tree": NormIndexBuilder._build_tree(entries),
        }

    @staticmethod
    def _slice_commentary_for_scope(
        baseline: dict,
        *,
        chapter_label: str | None,
    ) -> dict:
        if chapter_label is None:
            return baseline
        prefix = f"{chapter_label}."
        entries = [
            entry
            for entry in baseline.get("entries", [])
            if entry.get("label") == chapter_label
            or str(entry.get("label", "")).startswith(prefix)
        ]
        commentary_map = {
            label: text
            for label, text in dict(baseline.get("commentary_map", {}) or {}).items()
            if label == chapter_label or str(label).startswith(prefix)
        }
        return {
            "summary_text": str(baseline.get("summary_text", "")),
            "entries": entries,
            "tree": NormAiScopePatcher._build_tree(entries),
            "commentary_map": commentary_map,
            "errors": list(baseline.get("errors", [])),
        }

    @staticmethod
    def _slice_markdown_for_scope(
        *,
        markdown_text: str,
        chapter_label: str | None,
    ) -> str:
        if chapter_label is None or not markdown_text.strip():
            return markdown_text
        lines = markdown_text.splitlines()
        start_idx = None
        end_idx = len(lines)
        chapter_heading = f"# {chapter_label} "
        section_heading = f"## {chapter_label}."

        for idx, raw in enumerate(lines):
            stripped = raw.strip()
            if start_idx is None and (
                stripped.startswith(chapter_heading)
                or stripped == f"# {chapter_label}"
                or stripped.startswith(section_heading)
            ):
                start_idx = idx
                continue

            if start_idx is not None and stripped.startswith("# "):
                if stripped.startswith(chapter_heading) or stripped == f"# {chapter_label}":
                    continue
                end_idx = idx
                break

        if start_idx is None:
            return markdown_text
        return "\n".join(lines[start_idx:end_idx]).strip()

    @staticmethod
    def _slice_page_texts_for_scope(
        *,
        page_texts: list[dict],
        clause_index: dict,
        commentary_result: dict,
        chapter_label: str | None,
    ) -> list[dict]:
        if chapter_label is None:
            return page_texts
        page_numbers: set[int] = set()
        for entry in clause_index.get("entries", []):
            start = entry.get("page_start")
            end = entry.get("page_end")
            if isinstance(start, int):
                page_numbers.add(start)
            if isinstance(end, int):
                page_numbers.add(end)
        for entry in commentary_result.get("entries", []):
            start = entry.get("page_start")
            end = entry.get("page_end")
            if isinstance(start, int):
                page_numbers.add(start)
            if isinstance(end, int):
                page_numbers.add(end)
        if not page_numbers:
            prefix = f"{chapter_label}."
            for item in page_texts:
                text = str(item.get("text", ""))
                page = item.get("page")
                if (
                    isinstance(page, int)
                    and (
                        f"{chapter_label} " in text
                        or prefix in text
                    )
                ):
                    page_numbers.add(page)
        if not page_numbers:
            return []
        return [
            item
            for item in page_texts
            if isinstance(item.get("page"), int) and item["page"] in page_numbers
        ]

    @staticmethod
    def _overlay_entry(baseline: dict, patch: dict) -> dict:
        # Keep structural + page fields from baseline; allow AI to improve text/tags.
        merged = dict(baseline)
        for key in ("summary_text", "tags", "commentary_summary", "content_preview"):
            if key in patch:
                merged[key] = patch.get(key)
        if not merged.get("title") and patch.get("title"):
            merged["title"] = patch.get("title")
        return merged

    @staticmethod
    def _eligible_new_label(
        label: str,
        expected_chapters: list[str],
        expected_sections: list[str],
    ) -> bool:
        if label in expected_chapters:
            return True
        if label in expected_sections:
            return True
        for chapter in expected_chapters:
            if chapter and label.startswith(f"{chapter}."):
                return True
        return False

    @staticmethod
    def _overlay_commentary_entry(baseline: dict, patch: dict) -> dict:
        merged = dict(baseline)
        for key in ("commentary_text", "summary_text", "tags"):
            if key in patch:
                merged[key] = patch.get(key)
        for key in ("page_start", "page_end", "parent_label", "title", "node_type"):
            if not merged.get(key) and patch.get(key) is not None:
                merged[key] = patch.get(key)
        return merged

    @staticmethod
    def _build_tree(entries: list[dict]) -> list[dict]:
        nodes = {
            entry["label"]: {**entry, "children": []}
            for entry in entries
            if entry.get("label")
        }
        roots: list[dict] = []
        for entry in entries:
            label = entry.get("label")
            if not label:
                continue
            node = nodes[label]
            parent_label = entry.get("parent_label")
            if parent_label and parent_label in nodes:
                nodes[parent_label]["children"].append(node)
            else:
                roots.append(node)
        return roots
