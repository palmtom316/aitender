from __future__ import annotations

from dataclasses import dataclass

from app.services.norm_index_builder import NormIndexBuilder


@dataclass(frozen=True)
class NormScope:
    name: str
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
        markdown_text: str,
        page_texts: list[dict],
        baseline_clause_index: dict,
        baseline_commentary_result: dict,
        expected_chapters: list[str],
        expected_sections: list[str],
        config,
    ) -> tuple[dict, dict]:
        scopes = self._plan_scopes(expected_chapters)
        baseline_by_label = {
            entry.get("label"): entry
            for entry in baseline_clause_index.get("entries", [])
            if entry.get("label")
        }
        merged_by_label = dict(baseline_by_label)

        for scope in scopes:
            scope_baseline = self._slice_baseline_for_scope(
                baseline_clause_index,
                chapter_label=scope.chapter_label,
            )
            clause_index_patch, commentary_patch = self._ai.generate(
                document_id=document_id,
                markdown_text=markdown_text,
                page_texts=page_texts,
                baseline_clause_index=scope_baseline,
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

            # Commentary patch is optional in Phase 1; keep the baseline by default.
            _ = commentary_patch

        merged_entries = list(merged_by_label.values())
        merged_entries.sort(key=lambda item: str(item.get("label", "")))
        tree = NormIndexBuilder._build_tree(merged_entries)

        return (
            {
                "summary_text": str(baseline_clause_index.get("summary_text", "")),
                "entries": merged_entries,
                "tree": tree,
            },
            baseline_commentary_result,
        )

    @staticmethod
    def _plan_scopes(expected_chapters: list[str]) -> list[NormScope]:
        chapters = [label for label in expected_chapters if label]
        if not chapters:
            return [NormScope(name="all", chapter_label=None)]
        return [
            NormScope(name=f"chapter-{label}", chapter_label=label)
            for label in chapters
        ]

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

