from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.repositories.json_state_store import JsonStateStore
from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.norm_label_utils import label_sort_key


class JsonNormStructureRepository(NormStructureRepository):
    def __init__(self, state_path: Path | None = None) -> None:
        self._store = JsonStateStore(
            state_path or settings.state_root / "norm_structure.json",
        )
        self._store.load(default_factory=self._default_state)

    def supports_persisted_search(self) -> bool:
        # Keep False for now so the pipeline still persists debug JSON artifacts.
        return False

    def reset(self) -> None:
        self._store.reset()
        self._store.load(default_factory=self._default_state)

    def replace_clause_entries(
        self,
        document_id: str,
        entries: list[NormClauseEntry],
    ) -> None:
        state = self._store.load(default_factory=self._default_state)
        path_labels_by_label = self._build_path_labels_by_label(entries)
        payload = []
        for entry in entries:
            row = entry.model_dump(mode="json")
            row["path_labels"] = path_labels_by_label.get(entry.label, [])
            payload.append(row)
        state["clause_entries"][document_id] = payload
        self._store.save(state)

    def replace_commentary_entries(
        self,
        document_id: str,
        entries: list[NormCommentaryEntry],
    ) -> None:
        state = self._store.load(default_factory=self._default_state)
        state["commentary_entries"][document_id] = [
            entry.model_dump(mode="json")
            for entry in entries
        ]
        self._store.save(state)

    def list_clause_entries(self, document_id: str) -> list[NormClauseEntry]:
        state = self._store.load(default_factory=self._default_state)
        return [
            NormClauseEntry.model_validate(item)
            for item in state["clause_entries"].get(document_id, [])
        ]

    def list_commentary_entries(
        self,
        document_id: str,
    ) -> list[NormCommentaryEntry]:
        state = self._store.load(default_factory=self._default_state)
        return [
            NormCommentaryEntry.model_validate(item)
            for item in state["commentary_entries"].get(document_id, [])
        ]

    def search_clause_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        entries = self.list_clause_entries(document_id)
        if not entries:
            return None

        results: list[dict] = []
        tokens = [token for token in (query or "").lower().split() if token]

        for entry in entries:
            if entry.node_type != "clause":
                continue
            if clause_id and entry.label != clause_id:
                continue
            if path_prefix and path_prefix not in (entry.path_labels or []):
                continue

            haystack = " ".join(
                [
                    entry.title or "",
                    entry.summary_text or "",
                    entry.commentary_summary or "",
                    entry.content_preview or "",
                ]
            ).lower()
            if tokens and not all(token in haystack for token in tokens):
                continue

            results.append(
                {
                    "label": entry.label,
                    "title": entry.title,
                    "page_start": entry.page_start,
                    "page_end": entry.page_end,
                    "summary_text": entry.summary_text,
                    "commentary_summary": entry.commentary_summary,
                    "content_preview": entry.content_preview,
                    "path_labels": list(entry.path_labels or []),
                    "tags": list(entry.tags or []),
                }
            )

        results.sort(key=lambda item: label_sort_key(item["label"]))
        return results

    def search_commentary_results(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> list[dict] | None:
        clause_entries = {entry.label: entry for entry in self.list_clause_entries(document_id)}
        commentary_entries = self.list_commentary_entries(document_id)
        if not commentary_entries:
            return None

        results: list[dict] = []
        tokens = [token for token in (query or "").lower().split() if token]

        for commentary in commentary_entries:
            if commentary.node_type != "clause":
                continue
            clause_entry = clause_entries.get(commentary.label)
            if clause_entry is None:
                continue
            if clause_id and commentary.label != clause_id:
                continue
            if path_prefix and path_prefix not in (clause_entry.path_labels or []):
                continue
            haystack = " ".join(
                [
                    commentary.commentary_text or "",
                    commentary.summary_text or "",
                ]
            ).lower()
            if tokens and not all(token in haystack for token in tokens):
                continue

            results.append(
                {
                    "label": clause_entry.label,
                    "title": clause_entry.title,
                    "page_start": clause_entry.page_start,
                    "page_end": clause_entry.page_end,
                    "summary_text": clause_entry.summary_text,
                    "commentary_summary": commentary.commentary_text,
                    "content_preview": clause_entry.content_preview,
                    "path_labels": list(clause_entry.path_labels or []),
                    "tags": list(clause_entry.tags or []),
                }
            )

        results.sort(key=lambda item: label_sort_key(item["label"]))
        return results

    @staticmethod
    def _default_state() -> dict:
        return {
            "clause_entries": {},
            "commentary_entries": {},
        }

    @staticmethod
    def _build_path_labels_by_label(
        entries: list[NormClauseEntry],
    ) -> dict[str, list[str]]:
        entry_by_label = {entry.label: entry for entry in entries}
        path_labels_by_label: dict[str, list[str]] = {}

        for entry in entries:
            path: list[str] = []
            current: NormClauseEntry | None = entry
            while current is not None:
                path.append(current.label)
                current = (
                    entry_by_label.get(current.parent_label)
                    if current.parent_label
                    else None
                )
            path_labels_by_label[entry.label] = list(reversed(path))

        return path_labels_by_label
